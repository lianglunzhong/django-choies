#-*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse,request
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import Customers,Point_Records,Address
from .models import User
from django.db.models import Q
import re
import time,datetime
from core.views import eparse,nowtime,write_csv,time_stamp,time_str,time_str2,time_stamp2,pp
from orders.models import Order,OrderItem
from django.db import connection, transaction
import demjson
import memcache
from django.contrib.auth.decorators import login_required
from django.conf import settings
# from django.core.cache import cache
from products.models import Product


def validateEmail(email):
    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1
    return 0

@login_required
def customer_points(request):
	data =  {}
	# print '---', request.user.id
	if request.POST.get('type') == 'points':
		emails = request.POST.get('customer_points','').strip().split('\r\n')
		points = request.POST.get('points','')
		record = request.POST.get('record','')
		user_id = request.user.id
		#验证是否为纯数字
		if points.isdigit():
			points = int(points)
			#积分不能为0
			if points:
				for email in emails:
					res = validateEmail(email)
					if res:

						arr = Customers.objects.filter(email=email,deleted=0).get()
						if arr:
							Point_Records.objects.create(customer_id=arr.id, amount=points, type=record,admin_id=user_id,status='activated')
							if arr.points:
								points = arr.points + points
							else:
								points = points
							Customers.objects.filter(id=arr.id).update(points=points)
							messages.success(request, u"操作成功")
						else:
							messages.error(request, u"用户%s不存在 " % email)

					else:
						messages.error(request, u"email格式不正确，请核对:%s"% email)
			else:
				messages.error(request, u"积分不能为0")
		else:
			messages.error(request, u"积分内容输入不正确，请核对")
	elif request.POST.get('type') == 'admin':
		emails = request.POST.get('email','').strip().split('\r\n')
		admin = request.POST.get('admin','')	
		admin_validate = validateEmail(admin)
		if admin_validate:
			try:
				arr = User.objects.filter(email=admin).get()
			except User.DoesNotExist:
				messages.error(request, u"负责人%s不存在 " % admin)
			else:
				for email in emails:
					email_validate = validateEmail(email)
					if email_validate:
						Customers.objects.filter(email=email,deleted=0).update(users_admin_id=arr.id)
						messages.success(request, u"操作成功 " )
					else:
						messages.error(request, u"用户%s不存在 " % email)
		else:
			messages.error(request, u"请核对admin邮箱 ")
	elif request.POST.get('type') == 'email':
		emails = request.POST.get('email','').strip().split('\r\n')
		print '-----'
		for email in emails:
			email_validate = validateEmail(email)
			if email_validate:
				try:
					query = Customers.objects.filter(email=email).get()
				
				except Customers.DoesNotExist:
					#email不存在
					Customers.objects.create(email=email,deleted=0,flag=4)
					messages.success(request, u"操作成功")
				else:
					#email存在
					if query:
						#deleted=1
						if query.deleted:
							messages.error(request, u"注意:用户%s曾经被删除过，现在未对其进行任何操作 !!" % email)
						#deleted=0
						else:
							messages.error(request, u"用户%s已存在 " % email)
						
			else:
				messages.error(request, u"请核对输入的email %s " % email)
	
	#按照积分数范围/是否fb注册导出用户
	elif request.POST.get('type') == 'export_point_customers':
		"""时间不输入默认为当天 """
		try:
			from_time = eparse(request.POST.get('from_time'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
			print from_time
			print to_time
		except Exception, e:
			messages.error(request,u'请输入正常的时间格式')

		point_from = request.POST.get('point_from', '0')
		if point_from:
			point_from = int(point_from)
		else:
			point_from = 0
		point_to = request.POST.get('point_to', '0')
		if point_to:
			point_to = int(point_to)
		else:
			point_to = 1000000

		submit = request.POST.get('submit', 'Export')
		is_facebook = int(request.POST.get('is_facebook','0'))

		print is_facebook
		if is_facebook == 1:
			customers = Customers.objects.filter(created__gte=from_time,created__lt=to_time,
				points__gte=point_from,points__lt=point_to,is_facebook=1)
			print customers
		else:
			customers = Customers.objects.filter(created__gte=from_time,created__lt=to_time,
				points__gte=point_from,points__lt=point_to)
			print customers

		if submit == 'Export':
			response, writer = write_csv('customers')
			writer.writerow(['created','email','firstname','points','country'])

			for customer in customers:
				country = ''
				if customer.country:
					country = customer.country
				else:
					address = Address.objects.filter(customer_id=customer.id).first()
					if address:
						country = address.country
				row = [
					str(customer.created),
					str(customer.email),
					str(customer.firstname),
					str(customer.points),
					str(country),
				]
				writer.writerow(row)
			return response

		else:
			response, writer = write_csv('customers')
			writer.writerow(['email','created','ip_country'])
			for customer in customers:
				row = [
					str(customer.email),
					str(customer.created),
					str(customer.ip_country),
				]
				writer.writerow(row)
			return response

	#按照注册/下单/国家代码导出相应用户
	elif request.POST.get('type') == 'export_by_country':
		"""时间不输入默认为当天 """
		try:
			from_time = eparse(request.POST.get('from_time'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
			print from_time
			print to_time
		except Exception, e:
			messages.error(request,u'请输入正常的时间格式')

		select_type = request.POST.get('select_type','register')
		country_code = request.POST.get('country_code','')

		print select_type
		if select_type == 'register':
			response, writer = write_csv('Register_customers')
			writer.writerow(['email','country','created','orders'])

			if country_code:
				customers = Customers.objects.filter(created__gte=from_time,created__lt=to_time,
					country=country_code,flag__in=[0,3]).order_by('id')
			else:
				customers = Customers.objects.filter(created__gte=from_time,created__lt=to_time,
					flag__in=[0,3]).order_by('id')

			for customer in customers:
				order_count = Order.objects.filter(customer_id=customer.id).count()
				row = [
					str(customer.email),
					str(customer.country),
					str(customer.created), #时间应该+8小时，待考虑
					str(order_count),
				]
				writer.writerow(row)
			return response
		elif select_type == 'order':
			response, writer = write_csv('Order_customers')
			writer.writerow(['Email','Country','created','Revenue'])

			if country_code:
				orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,shipping_country=country_code,
					payment_status__in=['verify_pass','success'],is_active=1).order_by('id')
			else:
				orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,
					payment_status__in=['verify_pass','success'],is_active=1).order_by('id')

			for order in orders:
				revenue = ''
				rate = float(order.rate)
				amount = float(order.amount)
				if rate:
					revenue = round(amount/rate,2)
				else:
					revenue = 'null'
				row = [
					str(order.email),
					str(order.shipping_country),
					str(order.created),
					str(revenue),
				]
				writer.writerow(row)
			return response

	#加入wishlist没下单的用户导出(15天)
	elif request.POST.get('type') == 'export_wishlist_buy_none':
		now = time.time()
		nowtime = now - (now % 86400) + time.timezone

		response, writer = write_csv('export_wishlist_buy_none')
		writer.writerow(['Customer','SKU','Time'])

		#开始时间
		start_time = int(nowtime) - 10*86400

		#查找15天内加入wishlist的用户和产品信息
		sql = "SELECT customer_id, product_id,created FROM accounts_wishlists WHERE created>"+str(start_time)+" order by customer_id,created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()

		none_buy = []
		for res in results:
			#用户和产品都存在再往下执行
			customer_id = int(res[0])
			product_id = int(res[1])
			created = int(res[2])
			if customer_id and product_id:
				#查询用户是否已购买过该产品
				has_buy = OrderItem.objects.filter(product_id=product_id,order__customer_id=customer_id,order__payment_status__in=('verify_pass','success'))
				# sql = "SELECT oi.product_id FROM orders_order o LEFT JOIN orders_orderitem oi ON o.id=oi.order_id WhERE o.customer_id="+str(customer_id)+" AND o.payment_status IN ('verify_pass','success') AND oi.product_id="+str(product_id)
				if not has_buy:
					none_buy.append([customer_id,product_id,created])
	
		for res in none_buy:
			#用户邮箱
			customer = Customers.objects.filter(id=res[0]).first()
			product = Product.objects.filter(id=res[1]).first()
			if customer and product:
				#时间转化
				try:
					created = time_str2(int(res[2]))
				except Exception as e:
					created = ''
				#产品status转化
				row = [
					str(customer.email),
					str(product.sku),
					str(created),
				]
				writer.writerow(row)

		return response


	#导出所有会员
	elif request.POST.get('type') == 'get_vip_all':
		response, writer = write_csv('vip_customers')
		writer.writerow(['email','is_vip','vip_start','vip_end','users_admin','updated',])

		customers = Customers.objects.filter(is_vip__gt=0)
		for customer in customers:
			vip_start = ''
			if customer.vip_start:
				vip_start = customer.vip_start
			vip_end = ''
			if 	customer.vip_end:
				vip_end = customer.vip_end

			updated = customer.updated
			admin = ''
			users_admin = User.objects.filter(id=customer.users_admin_id).first()
			if users_admin:
				admin = users_admin.username

			row = [
				str(customer.email),
				str(customer.is_vip),
				str(vip_start),
				str(vip_end),
				str(admin),
				str(updated),
			]
			writer.writerow(row)
		return response

	#导出现在有效的vip用户
	elif request.POST.get('type') == 'get_vip_all_valid':
		response, writer = write_csv('vip_customers')
		writer.writerow(['email','is_vip','vip_start','vip_end','users_admin','updated',])

		to_time = nowtime()
		to_time = time_stamp(to_time)
		print to_time

		customers = Customers.objects.filter(is_vip__gt=0)
		for customer in customers:
			vip_start = customer.vip_start
			vip_end = customer.vip_end
			updated = customer.updated
			admin = ''
			users_admin = User.objects.filter(id=customer.users_admin_id).first()
			if users_admin:
				admin = users_admin.username

			row = [
				str(customer.email),
				str(customer.is_vip),
				str(vip_start),
				str(vip_end),
				str(admin),
				str(updated),
			]
			writer.writerow(row)
		return response

	#按时间导出所有会员
	elif request.POST.get('type') == 'get_vip_all_bytime':
		try:
			from_time = eparse(request.POST.get('from_time'), offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'), offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception, e:
			messages.error(request,u'请输入正常的时间格式')

		response, writer = write_csv('vip_customers')
		writer.writerow(['email','created','vip_start','vip_end','ordernum','amount','orders_amount','users_admin','users_update'])

		customers = Customers.objects.filter(vip_start__gte=from_time,vip_start__lt=to_time,is_vip__gt=0).order_by('id')
		startvip = time_stamp('2015-01-01 00:00:00')

		for customer in customers:
			#订单查询时间过长，待改善
			# orders = Order.objects.filter(~Q(refund_status='refund'),email=customer.email,verify_date__gte=startvip,payment_status='verify_pass',is_active=1).order_by('verify_date')
			amount_vip = 0
			ordernum_vip = ''
			# for order in orders:
			# 	amount_vip += order.amount / order.rate
			# 	# 获取刚好满足199美元的订单
			# 	if amount_vip>199:
			# 		ordernum_vip=order.ordernum
			# 		break
			#历史消费总金额		
			orders_amount = 0
			# for order in orders:
			# 	orders_amount += order.amount / order.rate

			users_admin = ''
			user = User.objects.filter(id=customer.users_admin_id).first()
			if user:
				users_admin = user.username

			row = [
				str(customer.email),
				str(customer.created),
				str(customer.vip_start),
				str(customer.vip_end),
				str(ordernum_vip),
				str(amount_vip),
				str(orders_amount),
				str(users_admin),
				str(customer.updated),
			]
			writer.writerow(row)
		return response

	#按到期时间导出会员
	elif request.POST.get('type') == 'get_vip_by_expiredtime':
		vip_type = request.POST.get('vip_type','')

		now = time.time()
		nowtime = now - (now % 86400) + time.timezone

		response, writer = write_csv('get_vip_by_expiredtime')
		writer.writerow(['Email','vip_start','vip_end'])

		if vip_type:
			vip_type = int(vip_type)
			end_time = int(nowtime) + vip_type * 86400

			sql = "SELECT id,email,vip_start,vip_end FROM accounts_customers WHERE is_vip>0 and vip_end>="+str(int(now))+" and vip_end<"+str(end_time)+" ORDER BY id"
			cursor = connection.cursor()
			cursor.execute(sql)
			results = cursor.fetchall()

			for res in results:
				email = str(res[1])
				if email:
					#会员到期时间日期转化
					vip_start = int(res[2])
					vip_end = int(res[3])
					try:
						vip_start = time_str2(vip_start)
						vip_end = time_str2(vip_end)
					except Exception as e:
						vip_start = ''
						vip_end = ''

					row = [
						str(email),
						str(vip_start),
						str(vip_end)
					]
					writer.writerow(row)
			return response

	#用户报表页面导出下单两次及以上的用户
	elif request.POST.get('type') == 'order_twice_export':
		#获取缓存数据
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = 'customer_report'
		cache_content = cache.get(cache_key)
		if cache_content:
			response, writer = write_csv('order_twice_export')
			writer.writerow(['Email','Firstname','Lastname','Country','	Is_facebook'])

			data_export = cache_content['data_export']
			data_export = tuple(data_export)
			customers = Customers.objects.filter(id__in=data_export)
			for c in customers:
				row = [
					str(c.email),
					str(c.firstname),
					str(c.lastname),
					str(c.country),
					str(c.is_facebook),
				]
				writer.writerow(row)
			return response

	return render(request,'customer_points.html',data)

@login_required
def customer_report(request):
	data = {}

	now = time.time()
	nowtime = now - (now % 86400) + time.timezone
	last_week = int(nowtime) - 6*86400

	#获取缓存数据
	cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
	cache_key = 'customer_report'
	cache_content = cache.get(cache_key)
	if cache_content:
		data2 = {}
		data2['data'] = cache_content['data']

		return render(request,'customer_report.html',data2)
	else:
		#前一周时间列表
		'''
		day1 = time_str2(last_week)
		day2 = time_str2(last_week + 1*86400)
		day3 = time_str2(last_week + 2*86400)
		day4 = time_str2(last_week + 3*86400)
		day5 = time_str2(last_week + 4*86400)
		day6 = time_str2(last_week + 5*86400)
		day7 = time_str2(last_week + 6*86400)
		time_list = []
		time_list = [day1,day2,day3,day4,day5,day6,day7]
		'''
		#前两周时间列表
		last_week_before = int(nowtime) - 14*86400
		i = 0
		time_list = []
		while i < 14:
			time_list.append(time_str2(last_week_before + i*86400))
			i += 1
		# print time_list


		#当日注册数
		# sql = "SELECT FROM_UNIXTIME(created,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND created >"+str(last_week_before)+"  GROUP BY days"
		sql = "SELECT created,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND created >"+str(last_week_before)+"  GROUP BY created"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()

		customers = {}

		for res in results:
			order_day = time_str2(int(res[0]))
			if customers.has_key(str(order_day)):
				customers[str(order_day)] += int(res[1])
			else:
				customers[str(order_day)] = int(res[1])

		#字典按键排序（及日期升序排列）
		customers = sorted(customers.iteritems(),key=lambda d:d[0])

		#把查询结果赋值给字典
		register = {}
		register_counts = []

		for customer in customers:
			register[customer[0]] = customer[1]

		# #把查询结果赋值给字典
		# register = {}
		# register_counts = []
		# for result in results:
		# 	register[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			register.setdefault(day,0)
		#字典按键排序（即日期升序排列）
		register = sorted(register.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		register_json = []
		for reg in register:
			day = (time_stamp2(reg[0])+86400)*1000
			num = int(reg[1])
			register_json.append([day,num])
		# pp(register_json)
		# register_json = demjson.encode(register_json)
		data['register'] = register_json

		#当日注册并下单用户
		# sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days , COUNT(c.id) AS counts FROM orders_order o INNER JOIN accounts_customers c ON o.customer_id = c.id WHERE c.status=1 AND o.is_active=1 AND o.payment_status IN ('verify_pass','success') AND o.created > "+str(last_week_before)+" GROUP BY days "
		sql = "SELECT o.created AS days , COUNT(c.id) AS counts FROM orders_order o INNER JOIN accounts_customers c ON o.customer_id = c.id WHERE c.status=1 AND o.is_active=1 AND o.payment_status IN ('verify_pass','success') AND o.created > "+str(last_week_before)+" GROUP BY days "
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()

		customers = {}

		for res in results:
			order_day = time_str2(int(res[0]))
			if customers.has_key(str(order_day)):
				customers[str(order_day)] += int(res[1])
			else:
				customers[str(order_day)] = int(res[1])

		#字典按键排序（及日期升序排列）
		customers = sorted(customers.iteritems(),key=lambda d:d[0])


		#把查询结果赋值给字典
		register_order = {}
		for customer in customers:
			register_order[customer[0]] = customer[1]

		# for result in results:
		# 	register_order[result[0]] = result[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			register_order.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		register_order = sorted(register_order.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		register_order_json = []
		for reg in register_order:
			day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			register_order_json.append([day,num])
		# login_json = demjson.encode(login_json)
		data['register_order'] = register_order_json

		
		#当日登录
		# sql = "SELECT FROM_UNIXTIME(last_login_time,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND last_login_time >"+str(last_week_before)+"  GROUP BY days"
		sql = "SELECT last_login_time AS days ,COUNT(id) AS counts FROM accounts_customers WHERE status=1 AND last_login_time >"+str(last_week_before)+"  GROUP BY days"
		cursor = connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()

		customers = {}

		for res in results:
			order_day = time_str2(int(res[0]))
			if customers.has_key(str(order_day)):
				customers[str(order_day)] += int(res[1])
			else:
				customers[str(order_day)] = int(res[1])

		#字典按键排序（及日期升序排列）
		customers = sorted(customers.iteritems(),key=lambda d:d[0])
		#把查询结果赋值给字典
		login = {}
		login_counts = []
		for customer in customers:
			login[customer[0]] = customer[1]
		#判断结果在该时间范围内是否有空缺（即某一天没有值）
		for day in time_list:
			login.setdefault(day,0)
		#字典按键排序（及日期升序排列）
		login = sorted(login.iteritems(),key=lambda d:d[0])
		#把表格转换为曲线图：数据格式转化
		login_json = []
		for reg in login:
			day = time_stamp2(reg[0])*1000
			num = int(reg[1])
			login_json.append([day,num])
		# login_json = demjson.encode(login_json)
		data['login'] = login_json



		#注册用户总数
		register_tatol = Customers.objects.filter(created__lt=last_week_before,status=1).count()
		#把表格转换为曲线图：数据格式转化
		register_total_json = []
		tatal_num = register_tatol
		for reg in register:
			tatal_num += (reg[1])
			day = time_stamp2(reg[0])*1000
			num = int(tatal_num)
			register_total_json.append([day,num])
		data['register_total'] = register_total_json 
		

		#下过单用户占比
		#总用户数直接用上面的统计结果tatal_num
		sql = "SELECT o.customer_id AS cid, COUNT(o.customer_id) AS counts FROM  orders_order o INNER JOIN  accounts_customers c ON o.customer_id = c.id WHERE c.status=1 AND o.is_active=1 AND o.payment_status IN ('verify_pass','success') GROUP BY o.customer_id"
		print sql
		cursor =  connection.cursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		#下单用户总数统计
		order_customer = 0
		#下单两次及以上用户总数统计
		order_twice = 0
		#导出缓存数据
		data_export = []
		for res in results:
			order_customer += 1
			if res[1] > 1:
				order_twice += 1
				data_export.append(res[0])

		#数据整理
		order_customer_json = [['用户总数'.decode('utf8'),tatal_num],['下单用户数'.decode('utf8'),order_customer],['下单两次及以上用户数'.decode('utf8'),order_twice]]
		# order_twice_json = [['用户总数'.decode('utf8'),tatal_num],['order_twice',order_twice]]
		data['order_customer'] = order_customer_json
		# data['order_twice'] = order_twice_json

		#把数据转化为json格式
		data = demjson.encode(data)

		#设置缓存
		cache_data = {}
		cache_data['data'] = data
		cache_data['data_export'] = data_export
		cache.set(cache_key,cache_data,3*60*60)

		data2 = {}
		data2['data'] = data

		return render(request,'customer_report.html',data2)