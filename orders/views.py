#-*- coding: utf-8 -*-
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from orders.models import Order,OrderItem,OrderPayments,OrderShipments,OrderRemarks
from products.models import *
from django.db.models import Sum,F,Q
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from elasticsearch import Elasticsearch
from django.conf import settings
from dal import autocomplete
from accounts.models import Customers,Address
from orders.models import Order, OrderShipments,OrderHistories
from celebrities.models import Celebrits
from core.views import eparse,nowtime,write_csv,time_stamp,time_str2,time_str,time_stamp2,time_stamp3,time_stamp4,time_stamp5
from core.models import Country
from django.contrib.auth.models import User
from django.db import connection, transaction
import memcache,demjson,json,phpserialize,time,datetime,pprint
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
# from django.core.cache import cache
from django.conf import settings
import urllib
import urllib2
import json
import thread 


@login_required
def handle(request):
	data = {}
	#批量添加订单产品
	if request.POST.get('type','') == 'add_item2order':
		ordernums = request.POST.get('ordernums', '').strip().split('\r\n')
		sku = request.POST.get('sku', '').strip().split('\r\n')
		# attribute = request.POST.get('attribute', '').strip().split('\r\n')

		print ordernums
		# print sku[0]
		success_msg = ''
		error_msg = ''

		productitem = Productitem.objects.filter(sku=sku[0]).first()

		if productitem:
			product = Product.objects.filter(id=productitem.product_id).get()
			if product:
				for ordernum in ordernums:
					order = Order.objects.filter(ordernum=ordernum).get()
					if order:
						shipping_status = Order.objects.filter(ordernum=ordernum).values_list('shipping_status')
						if shipping_status[0][0] == 'shipped' or shipping_status[0][0] == 'delivered':
							messages.error(request, ordernum + u'已发运，无法添加产品，请重新下单')
						else:
							#create
							query_create = OrderItem.objects.get_or_create(order_id=order.id,product_id=product.id,name=product.name,sku=productitem.sku,
								price=product.price,cost=product.cost,quantity=1,attributes=productitem.attribute, item_id=productitem.id)
							if query_create:
								success_msg += ordernum + '创建成功; '
							else:
								error_msg += ordernum + '创建失败; '
					else:
						error_msg += ordernum + '订单不存在; '
				if success_msg:
					messages.success(request, success_msg+error_msg)
				else:
					messages.error(request,error_msg)

		else:
			messages.error(request,u'无产品')

	#查询(导出)order信息，输入order id 一行一个
	elif request.POST.get('type') == 'export_info_by_oids':
		orderids = request.POST.get('orderids','').strip().split('\r\n')
		print orderids

		#验证输入的order id是否全都正确
		orderidarr = []
		orderiderror = []
		for orderid in orderids:
			order = Order.objects.filter(id=orderid)
			if order:
				orderidarr.append(orderid)
			else:
				orderiderror.append(orderid)
		if orderiderror:
			messages.error(request,u'order id'+str(orderiderror)+u'有误，无此订单，请重新输入')
		#只在页面上展示，不做导出
		else:
			dataarr = {}
			header = ['order_id',u'交易号',u'币种',u'金额',u'支付时间']
			orderpayments = OrderPayments.objects.filter(order_id__in=orderidarr,payment_status='success').first()
			print '---',orderidarr,orderpayments
			dataarr['header'] = header
			dataarr['orderpayments'] = orderpayments
			return render(request,'export_info_by_oids.html',dataarr)

		#导出csv表格
		# else:
		# 	response, writer = write_csv('orderpayment_info')
		# 	writer.writerow(['order_id',u'交易号',u'币种',u'金额',u'支付时间'])
		# 	orderpayments = OrderPayments.objects.filter(order_id__in=orderidarr,payment_status='success')
		# 	for orderpayment in orderpayments:
		# 		row = [
		# 			str(orderpayment.order_id),
		# 			str(orderpayment.trans_id),
		# 			str(orderpayment.currency),
		# 			str(orderpayment.amount),
		# 			str(orderpayment.created),
		# 		]
		# 		writer.writerow(row)
		# 	return response

	#根据物流跟踪号查询(导出)order订单号，输入trackingcode 一行一个
	elif request.POST.get('type') == 'export_ordernum_by_trackingcode':

		codes = request.POST.get('trackingdodes','').strip().split('\r\n')

		#判断输入的物流跟踪号是否全都正确
		codearr = []
		code_error = []
		for code in codes:
			ordershipment = OrderShipments.objects.filter(tracking_code=code)
			if ordershipment:
				codearr.append(code)
			else:
				code_error.append(code)
		if code_error:
			messages.error(request,u'物流跟踪号'+str(code_error)+u'有误，请重新输入')
		#只在页面上展示，不做导出
		else:
			dataarr = {}
			header = ['tracking_code','ordernum']
			ordershipments = OrderShipments.objects.filter(tracking_code__in=codearr)
			dataarr['header'] = header
			dataarr['ordershipments'] = ordershipments
			return render(request,'export_ordernum_by_trackingcode.html',dataarr)
				
		#导出csv表格
		# else:
		# 	response, writer = write_csv('track_ordernum_info')
		# 	writer.writerow(['tracking_code','ordernum'])

		# 	ordershipments = OrderShipments.objects.filter(tracking_code__in=codearr)
		# 	for ordershipment in ordershipments:
		# 		row = [
		# 			str(ordershipment.tracking_code),
		# 			str(ordershipment.ordernum),
		# 		]
		# 		writer.writerow(row)
		# 	return response

	#通过ordernum批量查询物流信息
	elif request.POST.get('type') == 'export_tracking_code_by_ordernum':
		response, writer = write_csv('export_tracking_code_by_ordernum')
		writer.writerow(['OrderNum', 'Tracking_Code', 'Tracking_Link'])
		ordernums = request.POST.get('ordernums').strip().split('\r\n')
		for ordernum in ordernums:
			ordershipment = OrderShipments.objects.filter(ordernum=ordernum).order_by('-id').first()
			if ordershipment:
				row = [
					str(ordershipment.ordernum),
					str(ordershipment.tracking_code),
					str(ordershipment.tracking_link),
				]
			else:
				row = [
					str(ordernum),
					str(''),
					str(''),
				]
			writer.writerow(row)
		return response

	#导出订单
	elif request.POST.get('type') == 'export_order':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')

		response, writer = write_csv('order_status')
		writer.writerow(['Order No.','Transaction Id','SKU','Description','Qty','Attributes','Admin','Factory',
			'Taobao Url','Offline_factory','Stock','Country Code','Country','Remark','name','address','city','state',
			'zip','phone','mobile','Shipping amount','Amount','Email','Sale Price','Orig','Price','Total Cost','Time'])

		orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,is_active=1,payment_status__in=('verify_pass','success'))

		for order in orders:
			country_name = ''
			country = Country.objects.filter(isocode=order.shipping_country).first()
			if country:
				country_name = country.name

			#该字段查询太影响速度，暂时去掉
			# count = Order.objects.filter(email=order.email,payment_status__in=('verify_pass','success')).count()

			remarks = OrderRemarks.objects.filter(order_id=order.id).order_by('-created')
			remarkss = ''
			if remarks:
				for remark in remarks:
					remarkarr = {}
					remarkarr['remark'] = remark.remark
					user = User.objects.filter(id=remark.admin_id).first()
					if user:
						remarkarr['admin'] = user.username
						remarkss += remarkarr['remark']+'-'+remarkarr['admin']
					# else:
					# 	remarkss += remarkarr['remark']
				remarkss = remarkss[0:(len(remarkss)-1)]

			orderitems = OrderItem.objects.filter(order_id=order.id)
			for orderitem in orderitems:
				products = Product.objects.filter(id=orderitem.product_id)
				for product in products:
					row = [
						str(order.ordernum),
						str(order.transaction_id),
						str(orderitem.sku),
						str(product.description),
						str(orderitem.quantity),
						str(orderitem.attributes),
						str(''), #admin  
						str(product.factory),
						str(product.taobao_url),
						str(product.offline_factory),
						str(''),  #stock
						str(order.shipping_country), #Country Code
						str(country_name),
						str(remarkss),
						str(order.shipping_firstname+order.shipping_lastname),
						str(order.shipping_address),
						str(order.shipping_city),
						str(order.shipping_state),
						str(order.shipping_zip),
						str(order.shipping_phone),
						str(order.shipping_mobile),
						str(order.amount_shipping),
						str(order.amount),
						str(order.email),
						# str(count),
						str(orderitem.price),
						str(product.price),
						str(product.total_cost),
						str(order.created),
					]
					writer.writerow(row)
		return response

	#导出分类订单
	elif request.POST.get('type') == 'export_order_category':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')

		response, writer = write_csv('order_status')
		writer.writerow(['Order No',u'是否手机订单','Currency','Amount','Email','Admin','Created','Verify Date'])

		orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,is_active=1,payment_status__in=['success','verify_pass'])

		for order in orders:
			#该字段查询太影响速度，暂时去掉
			# count = Order.objects.filter(email=order.email,payment_status__in=['success','verify_pass']).count()
			is_mobile = u'否'
			if int(order.erp_fee_line_id) == 1:
				is_mobile = u'是'

			row = [
				str(order.ordernum),
				str(is_mobile),
				str(order.currency),
				str(order.amount),
				str(order.email),
				str(''),  #admin
				# str(count),
				str(order.created),
				str(order.verify_date),
			]
			writer.writerow(row)
		return response

	#订单跟踪链接统计导出
	elif request.POST.get('type') == 'export_status':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')

		response, writer = write_csv('order_status')
		writer.writerow(['Order No','Payment Status','Shipping Status','Tracking Code','Tracking Link'])

		payment_method = request.POST.get('payment_method','PP')
		orders = Order.objects.filter(verify_date__gte=from_time,verify_date__lt=to_time,payment_method=payment_method,
			shipping_status='shipped').order_by('-payment_status')
		for order in orders:
			ordershipments = OrderShipments.objects.filter(order_id=order.id)
			for ordershipment in ordershipments:
					row = [
						str(order.ordernum),
						str(order.payment_status),
						str(order.shipping_status),
						str(ordershipment.tracking_code),
						str(ordershipment.tracking_link),
					]
					writer.writerow(row)
		return response

	#导出订单详情
	elif request.POST.get('type') == 'export_order_detail':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59") or nowtime()
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')
		print from_time
		print to_time

		date_type = request.POST.get('date_type','')
		print date_type

		if date_type == 'order_date':
			response, writer = write_csv('order_detail')
			writer.writerow([u'下单时间',u'付款状态',u'验证通过时间',u'订单号',u'邮箱',u'国家',
				'Currency',u'订单总额',u'邮费',u'折扣号码',u'折扣号减免金额',u'使用积分',u'积分减免金额',u'购买产品sku',
				u'购买尺码',u'选款人',u'所属set','Product price',u'Price（销售价)',u'成本',u'重量',u'数量',u'运费险'])


			# orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,payment_status='verify_pass').order_by('-created')
			orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,).order_by('-created')
			for order in orders:
				orderitems = OrderItem.objects.filter(order_id=order.id)
				for orderitem in orderitems:
					products = Product.objects.filter(id=orderitem.product_id)
					for product in products:

						try:
							if product.offline_picker_id:
								offline_picker = product.offline_picker.username
							else:
								offline_picker = ''
						except Exception as e:
							offline_picker = ''

						try:
							if product.set_id:
								set_name = product.set.name
							else:
								set_name = ''
						except Exception as e:
							set_name = ''

						row = [
							str(order.created),
							str(order.payment_status),
							str(order.verify_date),
							str(order.ordernum),
							str(order.email),
							str(order.shipping_country),
							str(order.currency),
							str(order.amount),
							str(order.amount_shipping),
							str(order.coupon_code),
							str(order.amount_coupon),
							str(order.points),
							str(order.amount_point),
							str(product.sku),
							str(orderitem.attributes), #格式转换
							str(offline_picker),
							str(set_name),
							str(product.price),
							str(orderitem.price),
							str(product.total_cost),
							str(product.weight),
							str(orderitem.quantity),
							str(order.order_insurance),
						]
						writer.writerow(row)
			return response	
		else:
			response, writer = write_csv('order_detail')
			writer.writerow([u'下单时间',u'支付时间',u'支付状态',u'订单号',u'邮箱','Currency',u'订单总额',u'邮费',
				u'折扣号码',u'折扣号减免金额',u'使用积分',u'积分减免金额','IP',u'产品总数',
				u'发货国家',u'语言',u'支付方式',u'是否手机单',u'运费险'])
			
			# orderpayments =  OrderPayments.objects.filter(created__gte=from_time,created__lt=to_time,payment_status='verify_pass').order_by('-created')
			orderpayments =  OrderPayments.objects.filter(created__gte=from_time,created__lt=to_time,).order_by('-created')
			for orderpayment in orderpayments:
				orders = Order.objects.filter(id=orderpayment.order_id)
				for order in orders:
					#产品总数
					product_count = 0
					orderitems = OrderItem.objects.filter(order_id=order.id).all()
					for orderitem in orderitems:
						product_count += orderitem.quantity
					row = [
						str(order.created),
						str(orderpayment.created),
						str(order.payment_status),
						str(order.ordernum),
						str(order.email),
						str(order.currency),
						str(order.amount_order),
						str(order.amount_shipping),
						str(order.coupon_code),
						str(order.amount_coupon),
						str(order.points),
						str(order.amount_point),
						str(order.ip),
						str(product_count),
						str(order.shipping_country),
						str(order.lang),
						str(order.payment_method),
						str(order.erp_fee_line_id),
						str(order.order_insurance),
					]
					writer.writerow(row)
			return response
			
	#导出Wholesale用户订单
	elif request.POST.get('type') == 'export_wholesale':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')

		response, writer = write_csv('order_wholesale')
		writer.writerow(['ordernum','email','name','country','created','verify_date','payment_status',
			'currency','amount','admin','payment_method','lang'])

		orders = Order.objects.filter(~Q(email=''),created__gte=from_time,created__lt=to_time,order_from='wholesale')
		
		for order in orders:
			name = ''
			country = ''
			customer = Customers.objects.filter(id=order.customer_id).first()
			if customer:
				name = customer.firstname + customer.lastname
				country = customer.country

			row = [
				str(order.ordernum),
				str(order.email),
				str(name),
				str(country),
				str(order.created),
				str(order.verify_date),
				str(order.payment_status),
				str(order.currency),
				str(order.amount),
				str(''), #admin
				str(order.payment_method),
				str(order.lang),
			]
			writer.writerow(row)
		return response

	#导出大客户订单---单笔金额$200+
	elif request.POST.get('type') == 'export_amount200':
		try:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			messages.error(request,u'请输入正确的时间格式!')
			return redirect('order_handle')

		response, writer = write_csv('order_amount200')
		writer.writerow(['ordernum','email','name','country','created','verify_date','payment_status',
			'currency','rate','amount','amount_USD','admin','payment_method','lang'])

		orders = Order.objects.filter(~Q(email=''),created__gte=from_time,created__lt=to_time)
		for order in orders:
			amount_USD = order.amount/order.rate
			amount_USD = round(amount_USD,4)
			if amount_USD >= 200:
				name = ''
				country = ''
				customer = Customers.objects.filter(id=order.customer_id).first()
				if customer:
					name = customer.firstname + customer.lastname
					country = customer.country

				row = [
					str(order.ordernum),
					str(order.email),
					str(name),
					str(country),
					str(order.created),
					str(order.verify_date),
					str(order.payment_status),
					str(order.currency),
					str(order.rate),
					str(order.amount),
					str(amount_USD),
					str(''), #admin
					str(order.payment_method),
					str(order.lang),
				]
				writer.writerow(row)
		return response

	#使用折扣号的订单
	elif request.POST.get('type') == 'order_by_coupons':
		datas = {}
		coupons = request.POST.get('coupons', '').strip().split('\r\n')

		orderdata = []
		if coupons:
			orders = Order.objects.filter(coupon_code=coupons[0]).all().values_list('ordernum','amount','currency','created','payment_status').order_by('-created')
			if orders:
				for order in orders:
					created =  order[3].strftime('%Y-%m-%d %H:%M:%S')
					orderdata.append({u'ordernum':order[0],u'amount':order[1],u'currency':order[2],u'created':created,u'payment_status':order[4]})
				datas['orders'] = orderdata
				return render(request, 'order_by_coupons.html', datas)
	data['title']=''
	return render(request, 'order_handle.html', data)

#创建订单
@login_required
def add(request):
	data = {}
	if request.POST.get('type', '') == 'order_add':
		email = request.POST.get('email','').strip('')

		customer = Customers.objects.filter(email=email).first()

		#判断email客户是否存在
		if customer:
			customerid = customer.id
			#退货单
			is_backorder = request.POST.get('is_backorder','').strip('')
			parent_id = 0
			#获取退货单关联的订单号
			if is_backorder:
				ref_ordernum = request.POST.get('ref_ordernum','').strip('')	
				ref_order = Order.objects.filter(ordernum=ref_ordernum).order_by('-id').first()
				if ref_order:
					ref_orderid = ref_order.id
					parent_id = str(ref_orderid)
				else:
					messages.error(request, u'Reference Order '+ref_ordernum+' not found')
					return redirect('order_add')
			#获取其他输入信息
			shipping_method = request.POST.get('shipping_method','').strip('')
			payment_method = request.POST.get('payment_method','').strip('')
			order_from = request.POST.get('order_from','').strip('')

			#给定默认值，订单号用当前时间戳预填充，等订单创建成功后再更新
			currency = 'USD'
			created = nowtime()
			verify_date = nowtime()
			ordernum = str(int(time.time()))

			shipping_firstname = ''
			shipping_lastname = ''
			shipping_country = ''
			shipping_state = ''
			shipping_city = ''
			shipping_address = ''
			shipping_zip = ''
			shipping_phone = ''

			billing_firstname = ''
			billing_lastname = ''
			billing_country = ''
			billing_state = ''
			billing_city = ''
			billing_address = ''
			billing_zip = ''
			billing_phone = ''

			#获取客户地址
			address = Address.objects.filter(customer_id=customerid).order_by('-id').first()
			if address:
				shipping_firstname = address.firstname
				shipping_lastname = address.lastname
				shipping_country = address.country
				shipping_state = address.state
				shipping_city = address.city
				shipping_address = address.address
				shipping_zip = address.zip
				shipping_phone = address.phone

				billing_firstname = address.firstname
				billing_lastname = address.lastname
				billing_country = address.country
				billing_state = address.state
				billing_city = address.city
				billing_address = address.address
				billing_zip = address.zip
				billing_phone = address.phone
			#创建订单，因为订单号为当前时间戳，所以信息一定不会重复，无需用get_or_create
			query = Order.objects.create(
					email = email,
					ordernum = ordernum,
					customer_id = customerid,
					# parent_id = parent_id,
					currency = currency,
					shipping_method = shipping_method,
					payment_method = payment_method,
					verify_date = verify_date,
					order_from = order_from,
					shipping_firstname = shipping_firstname,
					shipping_lastname = shipping_lastname,
					shipping_country = shipping_country,
					shipping_state = shipping_state,
					shipping_city = shipping_city,
					shipping_address = shipping_address,
					shipping_zip = shipping_zip,
					shipping_phone = shipping_phone,
					billing_firstname = billing_firstname,
					billing_lastname = billing_lastname,
					billing_country = billing_country,
					billing_state = billing_state,
					billing_city = billing_city,
					billing_address = billing_address,
					billing_zip = billing_zip,
					billing_phone = billing_phone,
					created = created,
				)
			#订单创建成功，更新订单号
			if query:
				orderid = query.id
				ordernum = str(1)+str(orderid)+str(1340)
				query_update = Order.objects.filter(id=orderid).update(ordernum=ordernum)
				#退货单更新parent_id
				if parent_id:
					query_updated = Order.objects.filter(id=orderid).update(parent_id=parent_id)
					#信息更新成功，跳转到订单修改详情页
					return redirect('/admin/orders/order/'+str(orderid)+'/change/')
				else:
					return redirect('/admin/orders/order/'+str(orderid)+'/change/')
			else:
				messages.error(request,u'创建订单失败')
				return redirect('order_add')
		else:
			messages.error(request,u'Customer '+email+' not found')
			return redirect('order_add')

	#根据email批量创建订单
	if request.POST.get('type', '') == 'order_allcreate':
		emails = request.POST.get('allcreate_eamil','').strip().split('\r\n')

		#判断是否有输入
		if emails[0]:
			email_error = ''
			create_error = ''
			for email in emails:
				customer = Customers.objects.filter(email=email).first()
				if customer:
					customerid = customer.id

					shipping_method = ''
					payment_method = 'PP'
					order_from = 'activity'

					payment_status = 'verify_pass'
					currency = 'USD'
					# parent_id = ''
					verify_date = nowtime()
					#用时间戳来预填充订单号，等订单创建成功之后再更改
					ordernum = str(int(time.time())) #

					#地址，默认值都设置为空
					shipping_firstname = ''
					shipping_lastname = ''
					shipping_country = ''
					shipping_state = ''
					shipping_city = ''
					shipping_address = ''
					shipping_zip = ''
					shipping_phone = ''

					billing_firstname = ''
					billing_lastname = ''
					billing_country = ''
					billing_state = ''
					billing_city = ''
					billing_address = ''
					billing_zip = ''
					billing_phone = ''

					#查询客户地址
					address = Address.objects.filter(customer_id=customerid).order_by('-id').first()
					if address:
						shipping_firstname = address.firstname
						shipping_lastname = address.lastname
						shipping_country = address.country
						shipping_state = address.state
						shipping_city = address.city
						shipping_address = address.address
						shipping_zip = address.zip
						shipping_phone = address.phone

						billing_firstname = address.firstname
						billing_lastname = address.lastname
						billing_country = address.country
						billing_state = address.state
						billing_city = address.city
						billing_address = address.address
						billing_zip = address.zip
						billing_phone = address.phone

					#创建订单,因为订单号是用当前时间戳预填充的，所以订单肯定不会重复，不需要用get_or_create
					query = Order.objects.create(
							email = email,
							ordernum = ordernum,
							customer_id = customerid,
							# parent_id = parent_id,
							currency = currency,
							shipping_method = shipping_method,
							payment_method = payment_method,
							payment_status = payment_status,
							verify_date = verify_date,
							order_from = order_from,
							shipping_firstname = shipping_firstname,
							shipping_lastname = shipping_lastname,
							shipping_country = shipping_country,
							shipping_state = shipping_state,
							shipping_city = shipping_city,
							shipping_address = shipping_address,
							shipping_zip = shipping_zip,
							shipping_phone = shipping_phone,
							billing_firstname = billing_firstname,
							billing_lastname = billing_lastname,
							billing_country = billing_country,
							billing_state = billing_state,
							billing_city = billing_city,
							billing_address = billing_address,
							billing_zip = billing_zip,
							billing_phone = billing_phone,
						)
					if query:
						orderid = query.id
						ordernum = str(1)+str(orderid)+str(1340)
						query_update = Order.objects.filter(id=orderid).update(ordernum=ordernum)

						#订单创建成功，更新orders_orderrmarks表
						admin_id = request.user.id
						remark = u'9610项目,发WXEUB'
						#保证新增的信息不重复
						created = nowtime()
						query, is_created = OrderRemarks.objects.get_or_create(remark=remark,admin_id=admin_id,order_id=orderid,created=created)
					else:
						create_error += email+':创建订单失败;  '
				else:
					email_error += email + ':对应的客户不存在;  '
			#最后判断是否有错误的email或者创建失败的订单
			message_error = ''
			message_error = email_error + create_error
			if message_error:
				messages.error(request,message_error)
				return redirect('order_add')
			else:
				messages.success(request, u'订单批量创建成功')
				return redirect('order_add')
		else:
			messages.error(request, u'请输入email')
			return redirect('order_add')

	return render(request, 'order_add.html', data)

@login_required
def report(request):
	data = {}
	data2 = []
	now = time.time()
	nowtime = now - (now % 86400) + time.timezone

	#判断是否为ajax提交的数据
	if request.method == 'POST':
		#订单支付状态统计
		if request.POST['type'] == 'payment_status_report':
			#获取提交的数据信息
			#时间范围
			from_time =  request.POST['from']
			if from_time:
				from_time = eparse(from_time, offset=" 00:00:00")
				from_time = time_stamp(from_time)
			else:
				from_time = int(nowtime) - 30 * 86400

			to_time = request.POST['to']
			if to_time:
				to_time = eparse(to_time, offset=" 23:59:59")
				to_time = time_stamp(to_time)
			else:
				to_time = int(now)
			#日期类型
			order_date = request.POST['date']
			if order_date == 'day':
				date = "(created,'%Y-%m-%d') AS date, "
			if order_date == 'week':
				date = "(created,'%w') AS date, "
			if order_date == 'month':
				date = "(created,'%Y-%m') AS date, "
			if order_date == 'year':
				date = "(created,'%Y') AS date, "

			#订单支付状态
			payment_status = request.POST['payment_status']
			#统计结果
			order_result = request.POST['result']
			if order_result == 'numbers':
				res = 'COUNT(*) AS num'
			else:
				res = 'sum(IFNULL(amount,0)/rate) AS amount'

			#订单类型
			order_type = request.POST['order_type']
			#采购订单
			if order_type == 'order':
				# sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order WHERE is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" AND rate != '' GROUP BY date"
				sql = "SELECT created, "+res+" FROM orders_order WHERE is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" AND rate != '' GROUP BY created"
			#红人订单
			if order_type == 'order_celebrity':
				if order_date == 'day':
					date = "(o.created,'%Y-%m-%d') AS date, "
				if order_date == 'week':
					date = "(o.created,'%w') AS date, "
				if order_date == 'month':
					date = "(o.created,'%Y-%m') AS date, "
				if order_date == 'year':
					date = "(o.created,'%Y') AS date, "
					
				if order_result == 'numbers':
					res = 'COUNT(o.id) AS num'
				else:
					res = 'sum(IFNULL(o.amount,0)/rate) AS amount'

				# sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order o ,celebrities_celebrits c WHERE o.customer_id = c.customer_id AND o.is_active=1 AND o.payment_status='"+payment_status+"' AND o.created >"+str(from_time)+" AND o.created < "+str(to_time)+" GROUP BY date"
				sql = "SELECT o.created, "+res+" FROM orders_order o ,celebrities_celebrits c WHERE o.customer_id = c.customer_id AND o.is_active=1 AND o.payment_status='"+payment_status+"' AND o.created >"+str(from_time)+" AND o.created < "+str(to_time)+" GROUP BY o.created"
			#手机订单
			if order_type == 'order_mobile':
				sql = "SELECT created, "+res+" FROM orders_order WHERE erp_fee_line_id=1 AND  is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY created"
				print sql
			#电脑订单
			if order_type == 'order_usual':
				sql = "SELECT created, "+res+" FROM orders_order WHERE erp_fee_line_id =0 AND  is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY created"

			#执行sql,查询结果处理
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()

			orders = {}
			data2 = []
			data3 = []
			for res in results:
				order_day = time_str2(int(res[0]))
				if orders.has_key(str(order_day)):
					orders[str(order_day)] += int(res[1])
				else:
					orders[str(order_day)] = int(res[1])

			#字典按键排序（及日期升序排列）
			orders = sorted(orders.iteritems(),key=lambda d:d[0])

			print orders

			for order in orders:
				day = (time_stamp2(order[0])+86400)*1000
				num = int(order[1])
				data2.append([day,num])
				data3.append([str(order[0]),num])

			'''
			data2 = []
			data3 = []
			for result in results:
				if order_date == 'day':
					day = (time_stamp2(result[0])+86400)*1000
				if order_date == 'week':
					day = time_stamp5(result[0])*1000
				if order_date == 'month':
					day = time_stamp3(result[0])*1000
				if order_date == 'year':
					day = time_stamp4(result[0])*1000
				num = int(result[1])
				data2.append([day,num])
				data3.append([str(result[0]),num])
			'''

			#设置缓存，用于导出
			cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
			cache_key = 'payment_status_export'
			cache_data = {}
			cache_data['data'] = data3
			cache_data['order_date'] = order_date
			cache_data['order_type'] = order_type
			cache_data['payment_status'] = payment_status
			cache_data['order_result'] = order_result
			cache.set(cache_key,cache_data,10*60)

			data['data'] = data2
			data = demjson.encode(data)
			return HttpResponse(data,content_type="application/json")

		#订单退款状态统计
		if request.POST['type'] == 'refund_status_report':
			#获取提交的数据信息
			#时间范围
			from_time =  request.POST['from']
			if from_time:
				from_time = eparse(from_time, offset=" 00:00:00")
				from_time = time_stamp(from_time)
			else:
				from_time = int(nowtime) - 30 * 86400

			to_time = request.POST['to']
			if to_time:
				to_time = eparse(to_time, offset=" 23:59:59")
				to_time = time_stamp(to_time)
			else:
				to_time = int(now)
			#日期类型
			refund_date = request.POST['date']
			if refund_date == 'day':
				date = "(updated,'%Y-%m-%d') AS date, "
			if refund_date == 'week':
				date = "(updated,'%w') AS date, "
			if refund_date == 'month':
				date = "(updated,'%Y-%m') AS date, "
			if refund_date == 'year':
				date = "(updated,'%Y') AS date, "
			#退款状态
			refund_status = request.POST['refund_status']
			if refund_status == 'refund':
				status = "refund_status = 'refund' "
			if refund_status == 'partial_refund':
				status = "refund_status = 'partial_refund' "
			if refund_status == 'sum':
				status = "refund_status IN ('refund','partial_refund') "
			#统计结果
			refund_result = request.POST['result']
			if refund_result == 'numbers':
				res = 'COUNT(*) AS num '
			else:
				res = 'sum(IFNULL(amount,0)/rate) AS amount '

			#查询语句以及执行
			sql = "SELECT updated, "+res+" FROM orders_order WHERE "+status+" AND updated > "+str(from_time)+" AND updated < "+str(to_time)+" GROUP BY updated"
			print sql
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()
			#对查询结果集处理
			orders = {}
			data2 = []
			data3 = []
			for res in results:
				order_day = time_str2(int(res[0]))
				if orders.has_key(str(order_day)):
					orders[str(order_day)] += int(res[1])
				else:
					orders[str(order_day)] = int(res[1])

			#字典按键排序（及日期升序排列）
			orders = sorted(orders.iteritems(),key=lambda d:d[0])

			for order in orders:
				day = (time_stamp2(order[0])+86400)*1000
				num = int(order[1])
				data2.append([day,num])
				data3.append([str(order[0]),num])

			'''
			data2 = []
			data3 = []
			for result in results:
				if refund_date == 'day':
					day = (time_stamp2(result[0])+86400)*1000
				if refund_date == 'week':
					day = time_stamp5(result[0])*1000
				if refund_date == 'month':
					day = time_stamp3(result[0])*1000
				if refund_date == 'year':
					day = time_stamp4(result[0])*1000
				num = int(result[1])
				data2.append([day,num])
				data3.append([str(result[0]),num])
			'''

			#设置缓存，用于导出
			cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
			cache_key = 'refund_status_export'
			cache_data = {}
			cache_data['data'] = data3
			cache_data['refund_date'] = refund_date
			cache_data['refund_status'] = refund_status
			cache_data['refund_result'] = refund_result
			cache.set(cache_key,cache_data,10*60)

			data['data'] = data2
			data = demjson.encode(data)
			return HttpResponse(data,content_type="application/json")

		#订单发货国家统计
		if request.POST['type'] == 'shipping_country':
			#获取提交的数据信息
			#时间范围
			from_time =  request.POST['from']
			if from_time:
				from_time = eparse(from_time, offset=" 00:00:00")
				from_time = time_stamp(from_time)
			else:
				from_time = int(nowtime) - 30 * 86400

			to_time = request.POST['to']
			if to_time:
				to_time = eparse(to_time, offset=" 23:59:59")
				to_time = time_stamp(to_time)
			else:
				to_time = int(now)

			#该时间段内每个国家发货总数
			sql = "SELECT shipping_country,COUNT(id) as num FROM orders_order WHERE shipping_date > "+str(from_time)+" AND shipping_date < " +str(to_time)+" GROUP BY shipping_country"
			# sql = "SELECT FROM_UNIXTIME(shipping_date,'%Y-%m-%d') AS day,shipping_country,COUNT(id) as num FROM orders_order WHERE shipping_date > "+str(from_time)+" AND shipping_date < " +str(to_time)+" GROUP BY day"
			#执行sql,
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()
			total1 = {}
			total2 = []
			#结果处理
			for res in results:
				total1[str(res[0])] = int(res[1])

			#对字典按值排序，用于柱状图展示和导出,排序的结果为列表，里面包含元组
			sorts = sorted(total1.iteritems(),key=lambda d:d[1],reverse = True)
			#把列表中的元组转化为列表
			for s in sorts:
				total2.append(list(s))
			#截取发货国家数量排行前20，用于柱状图
			total_histogram = total2[0:30]
			#地图数据
			total_map = total2

			#设置缓存，用于导出
			cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
			cache_key = 'shipping_country_export'
			cache_data = {}
			cache_data['from_time'] = request.POST['from']
			cache_data['to_time'] = request.POST['to']
			cache_data['total2'] = total2
			cache_data['total2'] = total2
			cache_data['top_30'] = total_histogram
			cache.set(cache_key,cache_data,10*60)

			data = {}
			data['total_histogram'] = total_histogram
			data = demjson.encode(data)
			return HttpResponse(data, content_type="application/json")

		#新老客户下单统计
		if request.POST['type'] == 'newold_report':
			#时间范围
			from_time =  request.POST['from']
			if from_time:
				from_time = eparse(from_time, offset=" 00:00:00")
				from_time = time_stamp(from_time)
			else:
				from_time = int(nowtime) - 30 * 86400

			to_time = request.POST['to']
			if to_time:
				to_time = eparse(to_time, offset=" 23:59:59")
				to_time = time_stamp(to_time)
			else:
				to_time = int(now)
			#
			sql = "SELECT FROM_UNIXTIME(created, '%Y-%m-%d') AS days, customer_id, count(*) AS num FROM orders_order WHERE is_active=1 AND payment_status IN ('verify_pass','success') AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY days, customer_id"
			# sql = "SELECT created, customer_id, count(*) AS num FROM orders_order WHERE is_active=1 AND payment_status IN ('verify_pass','success') AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY created, customer_id"
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()
			# print results
			#订单总数
			order_total = []
			#新用户订单
			order_new = []
			#老客户订单
			order_old = []
			#日期
			date = []
			date_list = []
			#获取所查询的日期，（每一天）
			for r in results:
				if r[0] in date_list:
					pass
				else:
					date_list.append(r[0])
			#在每一天内去查询新老客户下单数
			for t in date_list:
				num1 = 0
				num2 = 0
				cus_id = []
				for r in results:
					if t == r[0]:
						#订单总数
						num1 += 1
						if r[2] > 1:
							num2 += 1
						else:
							cus_id.append(int(r[1]))
				if len(cus_id):
					if len(cus_id) > 1:
						cin = " IN "+str(tuple(cus_id))
					if len(cus_id) == 1:
						cin = " = "+str(cus_id[0])
					#统计当天购买次数为1的用户是否在当前之前有过订单，以用户id分组，统计的结果包含的个数即为今天的老客户的订单数（+num2）
					sql = "SELECT customer_id, count(*) AS num FROM orders_order WHERE is_active=1 AND payment_status IN ('verify_pass','success') AND created < "+str(time_stamp2(t))+" AND customer_id  "+cin+" GROUP BY customer_id"
					cursor = connection.cursor()
					cursor.execute(sql)
					querys = cursor.fetchall()
					i = 0
					for j in querys:
						i += 1
					#新用户下单数
					news = len(cus_id) - i
					#老客户下单数
					olds = int(i)+int(num2)
				else:
					news = 0
					olds = num2
				#最后把每天的数据存储在单独的列表中
				date.append(t)
				order_total.append(num1)
				order_new.append(news)
				order_old.append(olds)

			data['date'] = date
			data['order_total'] = order_total
			data['order_new'] = order_new
			data['order_old'] = order_old

			#设置缓存，用于导出
			cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
			cache_key = 'new_old_export'
			cache_data = {}
			cache_data['date'] = date
			cache_data['order_total'] = order_total
			cache_data['order_new'] = order_new
			cache_data['order_old'] = order_old
			cache.set(cache_key,cache_data,10*60)

			data = demjson.encode(data)
			return HttpResponse(data,content_type="application/json")

		#积分折扣号订单统计
		if request.POST['type'] == 'coupon_points_report':
			#时间范围
			from_time =  request.POST['from']
			if from_time:
				from_time = eparse(from_time, offset=" 00:00:00")
				from_time = time_stamp(from_time)
			else:
				from_time = int(nowtime) - 30 * 86400

			to_time = request.POST['to']
			if to_time:
				to_time = eparse(to_time, offset=" 23:59:59")
				to_time = time_stamp(to_time)
			else:
				to_time = int(now)
			#查询类型
			type2 = request.POST['type2']
			if type2 == 'points':
				select_type = " AND points > 0 "
				name = u'使用积分订单数'
			elif type2 == 'coupon':
				select_type = " AND coupon_code != '' "
				name = u'使用折扣号订单数'
			else:
				select_type = " AND (points > 0 or coupon_code != '') "
				name = u'使用积分或折扣号订单数'

			#执行语句
			# sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(*) AS num FROM orders_order WHERE is_active=1 AND payment_status IN ('verify_pass','success') AND created >"+str(from_time)+" AND created < "+str(to_time)+str(select_type)+" GROUP BY days"
			sql = "SELECT created ,COUNT(*) AS num FROM orders_order WHERE is_active=1 AND payment_status IN ('verify_pass','success') AND created >"+str(from_time)+" AND created < "+str(to_time)+str(select_type)+" GROUP BY created"
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()

			orders = {}
			for res in results:
				order_day = time_str2(int(res[0]))
				if orders.has_key(str(order_day)):
					orders[str(order_day)] += int(res[1])
				else:
					orders[str(order_day)] = int(res[1])

			#字典按键排序（及日期升序排列）
			orders = sorted(orders.iteritems(),key=lambda d:d[0])

			order_num = []
			for order in orders:
				day = str(order[0])
				num = int(order[1])
				order_num.append([day,num])

			data = {}
			data['data'] = order_num
			data['name'] = name

			'''
			order_num = []
			for r in results:
				day = str(r[0])
				num = int(r[1])
				order_num.append([day,num])
			data = {}
			data['data'] = order_num
			data['name'] = name
			'''

			#设置缓存，用于导出
			cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
			cache_key = 'coupon_points_export'
			cache_data = {}
			cache_data['data'] = order_num
			cache_data['from'] = request.POST['from']
			cache_data['to'] = request.POST['from']
			cache_data['name'] = name
			cache.set(cache_key,cache_data,10*60)

			data = demjson.encode(data)
			return HttpResponse(data,content_type="application/json")



	if request.POST.get('type') == 'order_report':
		#时间范围
		from_time =  request.POST.get('from')
		if from_time:
			from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
		else:
			from_time = int(nowtime) - 30 * 86400

		to_time = request.POST.get('to')
		if to_time:
			to_time = eparse(request.POST.get('to'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		else:
			to_time = int(now)

		#日期类型
		order_date = str(request.POST.get('order_date'))
		if order_date == 'day':
			date = "(created,'%Y-%m-%d') AS date, "
		if order_date == 'week':
			date = "(created,'%Y-%m:%w') AS date, "
		if order_date == 'month':
			date = "(created,'%Y-%m') AS date, "
		if order_date == 'year':
			date = "(created,'%Y') AS date, "


		#订单支付状态
		payment_status = str(request.POST.get('payment_status'))

		#查询统计结果
		order_result = str(request.POST.get('order_result'))
		if order_result == 'numbers':
			res = 'COUNT(*) AS num'
		else:
			res = 'sum(IFNULL(amount,0)/rate) AS amount'

		#订单类型
		order_type = str(request.POST.get('order_type'))
		#采购订单
		if order_type == 'order':
			sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order WHERE is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" AND rate != '' GROUP BY date"
		#红人订单
		if order_type == 'order_celebrity':
			if order_result == 'numbers':
				res = 'COUNT(o.id) AS num'
			else:
				res = 'sum(IFNULL(o.amount,0)/rate) AS amount'

			sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order o ,celebrities_celebrits c WHERE o.customer_id = c.customer_id AND o.is_active=1 AND o.payment_status='"+payment_status+"' AND o.created >"+str(from_time)+" AND o.created < "+str(to_time)+" GROUP BY date"
		#手机订单
		if order_type == 'order_mobile':
			sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order WHERE erp_fee_line_id=1 AND  is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY date"
		#电脑订单
		if order_type == 'order_usual':
			sql = "SELECT FROM_UNIXTIME"+date+str(' ')+res+" FROM orders_order WHERE erp_fee_line_id =0 AND  is_active=1 AND payment_status='"+payment_status+"' AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY date"

		#执行sql,查询结果处理
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		for result in results:
			if order_date == 'day':
				day = time_stamp2(result[0])*1000
			if order_date == 'week':
				day = time_stamp5(result[0])*1000
			if order_date == 'month':
				day = time_stamp3(result[0])*1000
			if order_date == 'year':
				day = time_stamp4(result[0])*1000
			num = int(result[1])
			data2.append([day,num])
	#默认设置（即第一次打开页面时所展示的数据）
	else:
		#时间范围，默认为最近30天
		from_time = int(nowtime) - 30 * 86400
		to_time = int(now)

		#日期类型
		order_date = 'day'

		#订单类型，默认为order，即所有的采购订单
		order_type = 'order'
		#订单支付状态 默认verify_pass
		payment_status = 'verify_pass'
		#查询统计结果，默认为订单数量
		order_result = 'numbers'
		

		sql = "SELECT created,COUNT(*) AS num FROM orders_order WHERE is_active=1 AND payment_status='verify_pass' AND created >"+str(from_time)+" AND created < "+str(to_time)+" GROUP BY created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()

		orders = {}
		for res in results:
			order_day = time_str2(int(res[0]))
			if orders.has_key(str(order_day)):
				orders[str(order_day)] += int(res[1])
			else:
				orders[str(order_day)] = int(res[1])

		#字典按键排序（及日期升序排列）
		orders = sorted(orders.iteritems(),key=lambda d:d[0])

		for order in orders:
			day = (time_stamp2(order[0])+86400)*1000
			num = int(order[1])
			data2.append([day,num])


		'''
		for result in results:
			day = (time_stamp2(result[0])+86400)*1000
			num = int(result[1])
			data2.append([day,num])
		'''

	data['data'] = demjson.encode(data2)
	data['payment_status'] = payment_status
	data['order_result'] = order_result
	data['order_type'] = order_type
	data['from_time'] = time_str2(from_time)
	data['to_time'] = time_str2(to_time)
	data['order_date'] = order_date
	
	return render(request, 'order_report.html', data)

@login_required
def dashboard(request):
	data2 = {}
	data = {}
	now = time.time()
	nowtime = now - (now % 86400) + time.timezone

	# start_time = 1474056696  #测试数据
	# end_time = 1474337154    #测试数据

	#今日统计开始时间和结束时间
	today_start = int(nowtime)
	today_end = int(now)

	last_week = int(nowtime) - 6 * 86400
	# last_week = 1474056696   #测试数据
	day1 = time_str2(last_week)
	day2 = time_str2(last_week + 1*86400)
	day3 = time_str2(last_week + 2*86400)
	day4 = time_str2(last_week + 3*86400)
	day5 = time_str2(last_week + 4*86400)
	day6 = time_str2(last_week + 5*86400)
	day7 = time_str2(last_week + 6*86400)
	time_list = []
	time_list = [day1,day2,day3,day4,day5,day6,day7]

	start_time = last_week 
	end_time = now 

	#++++缓存设置++++
	cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
	cache_key = 'dashboard'
	cache_content = cache.get(cache_key)

	if 0:
		data['orders'] = cache_content['orders']
		data['customers'] = cache_content['customers']
		data['data'] = cache_content['data']
	else:	
		#+++++饼状图+++++饼状图+++++饼状图+++++饼状图+++++饼状图+++++饼状图++++++饼状图+++++饼状图++++
		#订单支付状态饼状图分类：验证通过单、白单、、取消单、失败单、其他
		payment_status_list = ['verify_pass','new','cancel','failed','pending','success','verify_banned','other'] 
		#今日订单饼状图数据
		sql = "SELECT payment_status,COUNT(*) AS num FROM orders_order WHERE is_active=1 AND created > "+str(today_start)+" AND created < "+str(today_end)+" GROUP BY payment_status"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#处理查询结果
		payment_status = []
		i = 0
		for result in results:
			if result[0] in payment_status_list:
				payment_status.append([result[0],result[1]])
			else:
				i += result[1]
		payment_status.append(['other',i])
		#判断最后的结果分类和饼状图分类是否全等，缺少的分类数量补0，保证传递的数据完全正确
		payment_status_result = []
		for j in payment_status:
			payment_status_result.append(j[0])
		for i in payment_status_list:
			if i not in payment_status_result:
				payment_status.append([i,0])
		data2['order_payment_status'] = payment_status
		
		

		#产品饼状图分类：今日上新、下架、隐藏、销量、在架并显示的产品总数
		# product_list = ['onstock','outstock','hidden','saled','total']
		product_list = []
		onstock = Product.objects.filter(status=1,visibility=1,display_date__gte=today_start,display_date__lt=today_end).count()
		product_list.append(['onstock',onstock])

		outstock = Product.objects.filter(status=0,updated__gte=today_start,updated__lt=today_end).count()
		product_list.append(['outstock',outstock])

		hidden = Product.objects.filter(visibility=0,updated__gte=today_start,updated__lt=today_end).count()
		product_list.append(['hidden',hidden])

		#当日销量
		sql = "SELECT IFNULL(sum(i.quantity),0) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(today_start)+" AND o.created < "+str(today_end)
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		if results:
			saled = results[0][0]
		else:
			saled = 0
		product_list.append(['saled',saled])

		#在架并显示的产品总数
		onstock_vis = Product.objects.filter(visibility=1,status=1).count()
		product_list.append(['onstock_vis',onstock_vis])

		data2['product_list'] = product_list



		#verify订单发货状态饼状图
		#所有的发货状态（共6种）
		shipping_status_list = ['new_s','processing','partial_shipped','shipped','delivered','pickup'] 
		#今日发货状态饼状图数据获取
		sql = "SELECT shipping_status,COUNT(*) AS num FROM orders_order WHERE is_active=1 AND payment_status='verify_pass' AND created > "+str(today_start)+" AND created < "+str(today_end)+" GROUP BY shipping_status"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#处理查询结果
		shipping_status = []
		i = 0
		for result in results:
				shipping_status.append([result[0],result[1]])
		#判断最后的结果分类和饼状图分类是否全等，缺少的分类数量补0，保证传递的数据完全正确
		shipping_status_result = []
		for j in shipping_status:
			shipping_status_result.append(j[0])
		for i in shipping_status_list:
			if i not in shipping_status_result:
				shipping_status.append([i,0])
		#当日verify订单总数
		verify_total = Order.objects.filter(is_active=1,payment_status='verify_pass',created__gte=today_start,created__lt=today_end).count()
		shipping_status.append(['verify_total',verify_total])

		data2['shipping_status'] = shipping_status


		
		#+++++订单统计曲线图+++++订单统计曲线图+++++订单统计曲线图+++++订单统计曲线图+++++订单统计曲线图++++++
		#采购订单

		sql = "SELECT created ,COUNT(id) AS counts FROM orders_order WHERE products <> 'PMproducts' AND is_active=1 AND payment_status IN ('success', 'verify_pass') AND created >"+str(last_week)+"  GROUP BY created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		# print results
		order = {}
		order_counts = []
		for res in results:
			order_day = time_str2(int(res[0]))
			if order.has_key(str(order_day)):
				order[str(order_day)] += int(res[1])
			else:
				order[str(order_day)] = int(res[1])

		'''
		sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM orders_order WHERE products <> 'PMproducts' AND is_active=1 AND payment_status IN ('success', 'verify_pass') AND created >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		order = {}
		order_counts = []
		for result in results:
			order[result[0]] = result[1]
		print order
		'''
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			order.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		order = sorted(order.iteritems(),key=lambda d:d[0])
		#把结果用表格展示出来
		for i in order:
			order_counts.append(i[1])
		#把表格转换为曲线图：数据格式转化
		order_json = []
		for reg in order:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			order_json.append([day,num])
		data2['order'] = order_json


		#红人订单
		sql = "SELECT o.created,COUNT(o.id) AS counts FROM orders_order o ,celebrities_celebrits c WHERE o.products <> 'PMproducts' AND o.customer_id = c.customer_id AND o.is_active=1 AND o.payment_status IN ('success', 'verify_pass') AND o.created >"+str(last_week)+"  GROUP BY created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		# print results
		order_celebrity = {}
		order_celebrity_counts = []
		for res in results:
			order_day = time_str2(int(res[0]))
			if order_celebrity.has_key(str(order_day)):
				order_celebrity[str(order_day)] += int(res[1])
			else:
				order_celebrity[str(order_day)] = int(res[1])

		'''
		sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days ,COUNT(o.id) AS counts FROM orders_order o ,celebrities_celebrits c WHERE o.products <> 'PMproducts' AND o.customer_id = c.customer_id AND o.is_active=1 AND o.payment_status IN ('success', 'verify_pass') AND o.created >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		order_celebrity = {}
		order_celebrity_counts = []
		for result in results:
			order_celebrity[result[0]] = result[1]
		'''
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			order_celebrity.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		order_celebrity = sorted(order_celebrity.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		order_celebrity_json = []
		for reg in order_celebrity:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			order_celebrity_json.append([day,num])
		data2['order_celebrity'] = order_celebrity_json


		#手机订单
		sql = "SELECT created,COUNT(id) AS counts FROM orders_order WHERE erp_fee_line_id=1 AND products <> 'PMproducts' AND is_active=1 AND payment_status IN ('success', 'verify_pass') AND created >"+str(last_week)+"  GROUP BY created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		porder = {}
		porder_counts = []
		for res in results:
			order_day = time_str2(int(res[0]))
			if porder.has_key(str(order_day)):
				porder[str(order_day)] += int(res[1])
			else:
				porder[str(order_day)] = int(res[1])

		'''
		sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM orders_order WHERE erp_fee_line_id=1 AND products <> 'PMproducts' AND is_active=1 AND payment_status IN ('success', 'verify_pass') AND created >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		porder = {}
		porder_counts = []
		for result in results:
			porder[result[0]] = result[1]
		'''
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			porder.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		porder = sorted(porder.iteritems(),key=lambda d:d[0])
		#把结果用表格展示出来
		for i in porder:
			porder_counts.append(i[1])
		#把表格转换为曲线图：数据格式转化
		porder_json = []
		for reg in porder:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			porder_json.append([day,num])
		data2['porder'] = porder_json

		#电脑订单
		usual_counts = []
		usual_json = []
		i = 0
		for days in time_list:
			day = (time_stamp2(days)+86400)*1000
			# day = time_stamp2(days)*1000
			num = int(order_counts[i]-porder_counts[i])
			usual_json.append([day,num])
			i += 1
		data2['usual'] = usual_json


		#+++++用户统计曲线图+++++用户统计曲线图+++++用户统计曲线图+++++用户统计曲线图+++++用户统计曲线图++++++
		#当日注册数
		sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND created >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		register = {}
		register_counts = []
		for result in results:
			register[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			register.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		register = sorted(register.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		register_json = []
		for reg in register:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			register_json.append([day,num])
		# pp(register_json)
		# register_json = demjson.encode(register_json)
		data2['register'] = register_json

		

		#当日登录
		sql = "SELECT FROM_UNIXTIME(last_login_time,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND last_login_time >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		login = {}
		login_counts = []
		for result in results:
			login[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			login.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		login = sorted(login.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		login_json = []
		for reg in login:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			login_json.append([day,num])
		# login_json = demjson.encode(login_json)
		data2['login'] = login_json



		#注册用户总数
		# sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND created >"+str(last_week)+" GROUP BY days  "
		register_tatol = Customers.objects.filter(created__lt=last_week,status=1).count()
		#把表格转换为曲线图：数据格式转化
		register_total_json = []
		tatal_num = register_tatol
		for reg in register:
			tatal_num += (reg[1])
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(tatal_num)
			register_total_json.append([day,num])
		data2['register_total'] = register_total_json 
		
		
		#+++++产品统计曲线图+++++产品统计曲线图+++++产品统计曲线图+++++产品统计曲线图+++++产品统计曲线图++++++
		#当日上新数
		sql = "SELECT FROM_UNIXTIME(display_date,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		onstock = {}
		onstock_counts = []
		for result in results:
			onstock[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			onstock.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		onstock = sorted(onstock.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		onstock_json = []
		for reg in onstock:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			onstock_json.append([day,num])
		data2['onstock'] = onstock_json


		#当日下架数
		sql = "SELECT FROM_UNIXTIME(updated,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=0  AND updated >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		outstock = {}
		outstock_counts = []
		for result in results:
			outstock[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			outstock.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		outstock = sorted(outstock.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		outstock_json = []
		for reg in outstock:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			outstock_json.append([day,num])
		data2['outstock'] = outstock_json


		#当日隐藏数
		sql = "SELECT FROM_UNIXTIME(updated,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE  visibility=0 AND updated >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		hidden = {}
		hidden_counts = []
		for result in results:
			hidden[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			hidden.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		hidden = sorted(hidden.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		hidden_json = []
		for reg in hidden:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			hidden_json.append([day,num])
		data2['hidden'] = hidden_json


		#在架并显示产品总数
		#统计该日期之前的所有总数
		count_before = Product.objects.filter(updated__lte=last_week, visibility=1,status=1).count()
		#统计该日期范围内每天更新的总数
		sql = "SELECT FROM_UNIXTIME(updated,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND updated >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		on_vis = {}
		on_vis_count = []
		on_vis_counts = []
		for result in results:
			on_vis[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			on_vis.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		on_vis = sorted(on_vis.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		hidden_json = []
		for reg in on_vis:
			count_before += int(reg[1])
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = count_before
			hidden_json.append([day,num])
		data2['on_vis'] = hidden_json



		#当日销量
		sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days ,IFNULL(sum(i.quantity),0) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(last_week)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#把查询结果赋值给字典
		sale = {}
		sale_counts = []
		for result in results:
			sale[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			sale.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		sale = sorted(sale.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		sale_json = []
		for reg in sale:
			day = (time_stamp2(reg[0])+86400)*1000
			# day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			sale_json.append([day,num])
		data2['sale'] = sale_json


		#++++++最新订单列表++++++最新订单列表++++++最新订单列表++++++最新订单列表++++++最新订单列表++++++
		orders = Order.objects.filter(is_active=1,payment_status__in=['success', 'verify_pass']).order_by('-id')[:100]

		#++++++最新注册用户列表++++++最新注册用户列表++++++最新注册用户列表++++++最新注册用户列表+++++++
		customers = Customers.objects.filter(status=1).order_by('-id')[:100]


		#把数据传递到模板页面	
		data['orders'] = orders
		data['customers'] = customers
		data['data'] = demjson.encode(data2)
		cache_data = data
		cache.set(cache_key,cache_data,600)

	return render(request,'dashboard.html',data)

#订单报表页面的数据导出
@login_required
def report_export(request):
	data = {}
	#订单支付状态报表导出
	if request.POST.get('type') == 'payment_status_export':
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'payment_status_export'
		cache_content = cache.get(cache_key)
		if cache_content:
			data = cache_content['data']
			payment_status = cache_content['payment_status']
			order_date = cache_content['order_date']
			order_type = cache_content['order_type']
			order_result = cache_content['order_result']
			if order_result == 'numbers':
				res = u'数量'
			else:
				res = u'金额'
			response, writer = write_csv('payment_status_export')
			writer.writerow(['时间','日期类型','订单类型','订单支付状态',res])
			for i in data:
				row = [
					str(i[0]),
					str(order_date),
					str(order_type),
					str(payment_status),
					str(i[1]),
				]
				writer.writerow(row)
			return response

	#订单退款状态报表导出
	if request.POST.get('type') == 'refund_status_export':
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'refund_status_export'
		cache_content = cache.get(cache_key)
		if cache_content:
			data = cache_content['data']
			refund_status = cache_content['refund_status']
			refund_date = cache_content['refund_date']
			refund_result = cache_content['refund_result']
			if refund_result == 'numbers':
				res = u'数量'
			else:
				res = u'金额'
			response, writer = write_csv('refund_status_export')
			writer.writerow(['时间','日期类型','订单退款状态',res])
			for i in data:
				row = [
					str(i[0]),
					str(refund_date),
					str(refund_status),
					str(i[1]),
				]
				writer.writerow(row)
			return response

	#订单发货国家报表导出
	if request.POST.get('type') == 'shipping_country_export':
		#导出类型
		export_type = request.POST.get('shipping_export_type','')
		#获取缓存数据
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'shipping_country_export'
		cache_content = cache.get(cache_key)
		if cache_content:
			from_time = cache_content['from_time']
			to_time = cache_content['to_time']
			total2 = cache_content['total2']
			top_30 = cache_content['top_30']

			#发货前30国家及发货订单数
			if export_type == 'shipping_top30':
				title = from_time+'---'+to_time+'发货前30国家及发货订单数'
				response, writer = write_csv('shipping_top30')
				writer.writerow([title])
				writer.writerow(['国家代码','发货总数'])
				for i in top_30:
					row = [
						str(i[0]),
						str(i[1]),
					]
					writer.writerow(row)
				return response

			#该时间段内每个国家发货订单数
			if export_type == 'shipping_sum':
				title = from_time+'---'+to_time+'发货国家及发货订单数'
				response, writer = write_csv('shipping_sum')
				writer.writerow([title])
				writer.writerow(['国家代码','发货总数'])
				for i in total2:
					row = [
						str(i[0]),
						str(i[1]),
					]
					writer.writerow(row)
				return response

			#该时间段内每个国家每天发货订单数
			if export_type == 'shipping_day_sum':
				title = from_time+'---'+to_time+'发货国家每天发货订单数'
				response, writer = write_csv('shipping_day_sum')
				writer.writerow([title])
				writer.writerow(['发货日期','发货国家','发货总数'])

				#数据查询
				from_time = time_stamp(eparse(from_time, offset=" 00:00:00"))
				to_time = time_stamp(eparse(to_time, offset=" 23:59:59"))
				sql = "SELECT FROM_UNIXTIME(shipping_date, '%Y-%m-%d') AS days ,shipping_country,count(*) AS num FROM orders_order WHERE shipping_date > "+str(from_time)+" AND shipping_date < "+str(to_time)+" GROUP BY shipping_country , days ORDER BY days DESC"
				cursor =  connection.cursor()
				cursor.execute(sql)
				results = cursor.fetchall()
				for r in results:
					row = [
						str(r[0]),
						str(r[1]),
						str(r[2]),
					]
					writer.writerow(row)
				return response

	#新老客户下单导出
	if request.POST.get('type') == 'newold_export':
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'new_old_export'
		cache_content = cache.get(cache_key)
		if cache_content:
			date = cache_content['date']
			order_total = cache_content['order_total']
			order_new = cache_content['order_new']
			order_old = cache_content['order_old']
			data = []
			j = len(date)
			i = 0
			while i < j:
				data.append([date[i],order_total[i],order_new[i],order_old[i]])
				i += 1
			response, writer = write_csv('new_old_export')
			writer.writerow(['日期','订单总数','新客户订单数','老客户订单数'])
			for i in data:
				row = [
					str(i[0]),
					str(i[1]),
					str(i[2]),
					str(i[3]),
				]
				writer.writerow(row)
			return response

	#积分折扣号订单导出
	if request.POST.get('type') == 'coupon_points_export':
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'coupon_points_export'
		cache_content = cache.get(cache_key)
		if cache_content:
			data = cache_content['data']
			from_time = cache_content['from']
			to_time = cache_content['to']
			name = cache_content['name']
			title = from_time + '---' + to_time + ':'+ name 
			response, writer = write_csv('coupon_points_export')
			writer.writerow([title])
			writer.writerow(['日期','订单数'])
			for r in data:
				row = [
					str(r[0]),
					str(r[1]),
				]
				writer.writerow(row)
			return response


	return render(request, 'order_report_export.html', data)


#打开订单详情页时显示的订单产品信息
@login_required
def orderitem_add(request,id):
	data = {}
	orderitem = []
	url = request.get_full_path()
	urls = url.strip().split('/')
	order_id = int(urls[3])
	orderitems = OrderItem.objects.filter(order_id=order_id).all()
	#获取产品图片
	image_list = {}
	for o in orderitems:
		product = Product.objects.filter(id=o.product_id).first()
		link = settings.BASE_URL+'product/'+str(product.link)+'_p'+str(product.id)
		item = Productitem.objects.filter(sku=o.sku).first()
		if item:
			dist = {'id':o.id,'link': link, 'name':product.name, 'attributes': item.attribute, 'sku': product.sku, 'original_price': o.original_price,
			 'price': o.price, 'quantity': o.quantity, 'weight':o.weight,'status':o.status,'is_gift':o.is_gift,'created':o.created,'product_id':product.id}
		else:
			dist = {'id':o.id,'link': link, 'name': product.name, 'attributes': o.attributes, 'sku': product.sku,
					'original_price': o.original_price,
					'price': o.price, 'quantity': o.quantity, 'weight': o.weight, 'status': o.status,
					'is_gift': o.is_gift, 'created': o.created,'product_id':product.id}
		orderitem.append(dist)
		#保存产品图片的字段
		# config = product.configs
		# #反序列化，结果为字典
		# if config:
		# 	config = phpserialize.loads(config)
		# 	#对字典判断是否有默认图片
		# 	if config.has_key('default_image'):
		# 		if config['default_image']:
		# 			image_list[int(o.product_id)] = int(config['default_image'])
		# 	elif config.has_key('images_order'):
		# 		if config['images_order']:
		# 			image_list[int(o.product_id)] = int(config['images_order'].strip('').split(',')[0])
		# 使用默认图片
		pimage = ProductImage.objects.filter(product_id=product.id, is_default=1).order_by('position').first()
		# 默认图片不存在，使用第一张
		if not pimage:
			pimage = ProductImage.objects.filter(product_id=product.id).order_by('position').first()

		image_url = ''

		if pimage:
			image = pimage.image
			if image:
				image_url = settings.MEDIA_URL + str(image)
			else:
				image_url = settings.MEDIA_URL + 'pimages/' + str(pimage.id) + '.jpg'

		image_list[int(product.id)] = image_url
	print orderitem
	data['orderitems'] = orderitem
	data['image_list'] =image_list
	data['order_id'] = order_id

	return render(request, 'orderitem_add.html', data)

@login_required
def orderitem_add_ajax(request):
	data = {}

	#添加订单产品ajax操作
	if request.method == 'POST':
		#根据输入的sku获取产品attribute数据的AJAX操作
		# 此方法用不到，保留
		if request.POST['type'] == 'add_sku':
			data = {}
			sku = request.POST['sku']
			product = Product.objects.filter(sku=sku).order_by('-id').first()
			product_sku = ''
			size = []
			if product:
				product_sku = 'success'
				attribute = ProductAttribute.objects.filter(product_id=product.id).order_by('-id').first()
				if attribute:
					sizes = attribute.options
					if sizes:
						size = sizes.strip('').split(',')
			data['product_sku'] = product_sku
			data['size'] = size
			
		#添加产品弹窗数据获取及操作AJAX
		if request.POST['type'] == 'add_product':
			#获取传递过来的数据
			order_id = request.POST['order_id']
			sku = request.POST.get('sku')
			qty = request.POST.get('qty')
			price = request.POST.get('price')
			if not qty:
				qty = 1
			if not price:
				price = 0
			#数据都存在时，才进行操作
			if sku:
				#获取对应的item,(已经下架的产品item不支持添加)
				productitem = Productitem.objects.filter(sku=sku,status=1).first()
				if productitem:
					attribute = 'Size:' + productitem.attribute + ';'
					print attribute
					# product
					product = Product.objects.filter(id=productitem.product_id).order_by('-id').first()
					if product:
						#产品绝对链接
						link = "https://www.choies.com/product/" + product.link + "_p" +str(product.id)
						#更新数据
						orderitem,is_greated = OrderItem.objects.get_or_create(product_id=product.id,order_id=order_id,
																			   item_id=productitem.id,
																			   name=product.name,sku=productitem.sku,link=link,
																			   price=float(price),original_price=product.price,
																			   cost=product.cost,weight=product.weight,status='new',attributes=attribute)
						#判断订单详情中是否存在这条数据，如果存在，则quantity等于原来的数量加上现在的数量，不存在更新quantity，
						if is_greated:
							quantity = int(orderitem.quantity) + int(qty)
							query = OrderItem.objects.filter(id=orderitem.id).update(quantity=quantity)
						else:
							query = OrderItem.objects.filter(id=orderitem.id).update(quantity=qty)
						if query:
							data['status'] = 1
							data['message'] = u'添加成功'
					else:
						data['status'] = 0
						data['message'] = u'item没有对应的产品'
				else:
					data['status'] = 0
					data['message'] = u'item sku不存在或者已经下架，请核对。'
			else:
				data['status'] = 0
				data['message'] = u'item sku不能为空'
		#编辑产品时根据当前的order_id和orderitem_id获取产品的sku---size
		#此方法用不到，保留
		if request.POST['type'] == 'edit_sku':
			data = {}
			#数据获取
			order_id = request.POST['order_id']
			orderitem_id = request.POST['orderitem_id']
			#根据id查出产品sku,且一定存在，然后获取产品size
			orderitem = OrderItem.objects.filter(id=orderitem_id,order_id=order_id).first()
			product = Product.objects.filter(sku=orderitem.sku).order_by('-id').first()
			size = []
			attribute = ProductAttribute.objects.filter(product_id=product.id).order_by('-id').first()
			if attribute:
				sizes = attribute.options
				if sizes:
					size = sizes.strip('').split(',')
			data['size'] = size

		#编辑页面数据获取及更新操作
		if request.POST['type'] == 'edit_item':
			qty = request.POST.get('qty')
			price = request.POST.get('price')
			order_id = request.POST.get('order_id')
			orderitem_id = request.POST.get('orderitem_id')
			if qty and not price:
				orderitem = OrderItem.objects.filter(id=orderitem_id, order_id=order_id).update(quantity=qty)
				if orderitem:
					data['status'] = 1
				else:
					data['status'] = 0
					data['message'] = u'更新失败'
			elif not qty and price:
				orderitem = OrderItem.objects.filter(id=orderitem_id, order_id=order_id).update(price=price)
				if orderitem:
					data['status'] = 1
				else:
					data['status'] = 0
					data['message'] = u'更新失败'
			elif qty and price:
				#更新数据
				orderitem = OrderItem.objects.filter(id=orderitem_id,order_id=order_id).update(price=price,quantity=qty)
				if orderitem:
					data['status'] = 1
				else:
					data['status'] = 0
					data['message'] = u'更新失败'
			else:
				data['status']  = 0
				data['message'] = u'数据不能为空'
		#取消订单产品ajax数据获取及操作
		if request.POST['type'] == 'cancel_item':
			data = {}
			#数据获取
			order_id = request.POST['order_id']
			orderitem_id = request.POST['orderitem_id']
			#查询orderitem表，获取发货状态，未发货前都能取消订单产品
			#该数据一定存在，无需判断
			orderitem = OrderItem.objects.filter(id=orderitem_id,order_id=order_id).first()
			#发货状态
			status = ''
			if orderitem:
				status = orderitem.status
			#判断发货状态
			if status == 'shipped':
				data['status'] = 0
				data['message'] = u'该产品已发货，无法取消！'
			elif status == 'cancel':
				data['status'] = 0
				data['message'] = u'该产品已经取消过了，无需再次取消！'
			else:
				query = OrderItem.objects.filter(id=orderitem_id,order_id=order_id).update(status='cancel')
				if query:
					data['status'] = 1
				else:
					data['status'] = 0
					data['message'] = u'产品取消失败'

	return HttpResponse(json.dumps(data), content_type="application/json")


'''
	订单详情页产品报缺
	用ajax提交订单id和缺货产品id，然后调用前台接口发送邮件
'''
@login_required
def order_item_outstock_ajax(request):
	data = {}
	if request.method == "POST":
		if request.POST['type'] == "order_item_outstock":
			order_id = request.POST['order_id']
			item_list = request.POST['item_list']
			item_list = demjson.decode(item_list)

			item_ids = []
			for item in item_list:
				if item != None:
					item_ids.append(item)

			if order_id and len(item_ids)>0:
				#获取订单信息
				order = Order.objects.filter(id=int(order_id)).first()
				if order:
					if order.payment_status == 'success' or order.payment_status == 'verify_pass':
						#订单编辑人
						username = request.user.username
						user_id = request.user.id
						erp_line_status = u'缺货-'+str(username)

						updated_items = []
						updated_items2 = []
						for item_id in item_ids:
							#更新订单详情表的状态
							item_update = OrderItem.objects.filter(id=item_id).update(status='cancel',erp_line_status=erp_line_status)
							if item_update:
								orderitem = OrderItem.objects.filter(id=item_id).first()
								updated_items2.append(item_id)
								product_id = orderitem.product_id
								product = Product.objects.filter(id=product_id).first()
								if product:
									updated_items.append([orderitem.name,product.sku,orderitem.price,orderitem.attributes,orderitem.quantity])

						if updated_items and len(updated_items)>0:
							#调用接口发送邮件
							url = settings.BASE_URL+'adminapi/order_item_outstock_email'
							# url = 'http://local.oldchoies.com/adminapi/order_item_outstock_email'

							order_id = order.id
							order_id = demjson.encode(order_id)

							updated_items2 = ','.join(updated_items2)
							updated_items2 = demjson.encode(updated_items2)

							#更新OrderHistories表
							comment_skus = ''
							for item in updated_items:
								comment_skus += item[1]+";"

							comment_skus = comment_skus[0:len(comment_skus)-1]
							comment_skus = u"报缺:" + comment_skus

							order_id = order.id

							thread.start_new_thread(update_orderhistory, (order_id,user_id,comment_skus))
							thread.start_new_thread(send_mail, (order_id,updated_items2))

							data['result'] = u'success.'
							data = demjson.encode(data)
							return HttpResponse(data, content_type='application/json')


							# send_mail(order_id,updated_items2)

							# req = urllib2.Request(url)
							# response = urllib2.urlopen(req,urllib.urlencode({'order_id':order_id,'items':updated_items2}))


							#更新OrderHistories表
							# comment_skus = ''
							# for item in updated_items:
							# 	comment_skus += item[1]+";"

							# comment_skus = comment_skus[0:len(comment_skus)-1]
							# comment_skus = u"报缺:" + comment_skus

							# history_update = OrderHistories.objects.create(order_id=order.id,order_status='send baoque',admin_id=user_id,message=comment_skus)
							
						else:
							data['result'] = u'Failed!3'
							data = demjson.encode(data)
							return HttpResponse(data, content_type='application/json')
					else:
						data['result'] = u'This order payment status is not success!'
						data = demjson.encode(data)
						return HttpResponse(data, content_type='application/json')
				else:
					data['result'] = u'Failed!2'
					data = demjson.encode(data)
					return HttpResponse(data, content_type='application/json')
			else:
				data['result'] = u'Failed!1'
				data = demjson.encode(data)
				return HttpResponse(data, content_type='application/json')

		if request.POST['type'] == "baodeng":
			order_id = request.POST['order_id']
			day = request.POST['day']
			item_list = request.POST['item_list']
			item_list = demjson.decode(item_list)

			#item数据筛选并转为列表
			item_ids = []
			for item in item_list:
				if item != None:
					item_ids.append(item)

			if order_id and item_ids and day:
				order_id = demjson.encode(int(order_id))
				day = demjson.encode(int(day))
				#把列表转为字符串
				item_ids = ','.join(item_ids)
				item_ids = demjson.encode(item_ids)

				#调用接口发送邮件
				url = settings.BASE_URL+'adminapi/baodeng_email'
				# url = 'http://local.oldchoies.com/adminapi/baodeng_email'
				req = urllib2.Request(url)
				response = urllib2.urlopen(req,urllib.urlencode({'order_id':order_id,'items':item_ids,'day':day}))

				data['result'] = u"success."
				data = demjson.encode(data)
				return HttpResponse(data, content_type='application/json')

			else:
				data['result'] = u"Failed!1"
				data = demjson.encode(data)
				return HttpResponse(data, content_type='application/json')

	return HttpResponse('11111')


def send_mail(order_id,updated_items2):	
	#调用接口发送邮件
	url = settings.BASE_URL+'adminapi/order_item_outstock_email'
	# url = 'http://local.oldchoies.com/adminapi/order_item_outstock_email'
	req = urllib2.Request(url)
	response = urllib2.urlopen(req,urllib.urlencode({'order_id':order_id,'items':updated_items2}))


def update_orderhistory(order_id,user_id,comment_skus):
	#更新OrderHistories表
	history_update = OrderHistories.objects.create(order_id=order_id,order_status='send baoque',admin_id=user_id,message=comment_skus)




