# -*- coding: utf-8 -*-
from django.shortcuts import render
from celebrities.models import Celebrits,CelebrityBlogs
from django.contrib import messages
import time,datetime
from core.views import eparse,nowtime,write_csv,time_stamp,time_str
from django.contrib.auth.models import User
from django.db import connection, transaction
from products.models import Product, CelebrityImages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect


@login_required
def celebrity_export(request):
	data = {}
	#红人列表导出:
	if request.POST.get('type') == 'export_celebrits':
		try:
			from_time = eparse(request.POST.get('from_time'),offset=" 00:00:00")
			to_time = eparse(request.POST.get('to_time'),offset=" 23:59:59")
		except Exception,e:
			print e

		response, writer = write_csv('celebrits')
		writer.writerow(['id','name','email','country','gender','birthday','level','admin','created','is able','Blogs'])

		celebrits = Celebrits.objects.filter(created__gte=from_time,created__lt=to_time)

		for celebrit in celebrits:
			admin = ''
			user = User.objects.filter(id=celebrit.admin_id).first()
			if user:
				admin = user.username

			gender = 'Woman'
			if celebrit.sex == 1:
				gender = 'Man'

			blogs = ''
			celebrityblogs = CelebrityBlogs.objects.filter(celebrity_id=celebrit.id)
			for celebrityblog in celebrityblogs:
				blogs += celebrityblog.url+' , '

			row = [
				str(celebrit.id),
				str(celebrit.name),
				str(celebrit.email),
				str(celebrit.country),
				str(gender),
				str(celebrit.birthday),
				str(celebrit.level),
				str(admin),
				str(celebrit.created),
				str(celebrit.is_able),
				str(blogs),
			]
			writer.writerow(row)
		return response

	#红人订单产品导出:
	elif request.POST.get('type') == 'export_celebrity_order_products':
		try:
			from_time = eparse(request.POST.get('from_time'),offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'),offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			print e

		response, writer = write_csv('celebrits_order_products')
		writer.writerow(['Email','Name','Created','Ordernum','Verify_date','SKU','Price','Admin'])

		query = "SELECT c.email,c.name,o.created,o.ordernum,o.verify_date,i.sku,i.product_id,c.admin_id FROM celebrities_celebrits c,orders_order o,orders_orderitem i WHERE c.customer_id=o.customer_id AND o.id=i.order_id AND (o.payment_status='success' or o.payment_status='verify_pass') AND i.status != 'cancel' AND o.created >="+str(from_time)+" AND o.created <"+str(to_time)+" ORDER BY o.created"
		# query = "select id,name ,email from celebrities_celebrits where id < 10"
		cursor = connection.cursor()
		cursor.execute(query)
		res = cursor.fetchall()
		for i in res:
			created = ''
			if i[2]:
				created = time_str(i[2])

			verify_date = ''
			if i[4]:
				verify_date = time_str(i[4])
			admin = ''

			price = ''
			if i[6]:
				product = Product.objects.filter(id=i[6],status=1).first()
				if product:
					price = product.price

			if i[7]:
				user = User.objects.filter(id=i[7]).first()
				if user:
					admin = user.username

			row = [
				str(i[0]),
				str(i[1]),
				str(created),
				str(i[3]),
				str(verify_date),
				str(i[5]),
				str(price), #价格待确认
				str(admin),
			]
			writer.writerow(row)
		return response

	#导出红人秀链接:
	elif request.POST.get('type') == 'export_celebrity_urls':
		try:
			from_time = eparse(request.POST.get('from_time'),offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'),offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			print e

		response, writer = write_csv('export_celebrity_urls')
		writer.writerow(['Ordernum','Created','SKU','URL'])

		query = "SELECT P.ordernum, O.created, P.sku, P.url FROM celebrities_celebrityorder P LEFT JOIN orders_order O ON P.order_id = O.id WHERE O.created >= "+str(from_time)+" AND O.created < "+str(to_time)+" ORDER BY P.ordernum"
		cursor =connection.cursor()
		cursor.execute(query)
		res = cursor.fetchall()
		for i in res:
			created = ''
			if i[1]:
				created = time_str(i[1])

			row = [
				str(i[0]),
				str(created),
				str(i[2]),
				str(i[3]),
			]
			writer.writerow(row)
		return response

	#按admin导出红人订单:
	elif request.POST.get('type') == 'export_celebrity_orders':
		try:
			from_time = eparse(request.POST.get('from_time'),offset=" 00:00:00")
			from_time = time_stamp(from_time)
			to_time = eparse(request.POST.get('to_time'),offset=" 23:59:59")
			to_time = time_stamp(to_time)
		except Exception,e:
			print e
		admin_id = request.POST.get('admin_id','')

		response, writer = write_csv('export_celebrity_orders')
		writer.writerow(['Ordernum','Created','SKU','URL'])

		# query = "SELECT o.ordernum,o.id,o.shipping_date,c.admin_id,c.email,c.id FROM orders_order o,celebrities_celebrits c,orders_ordershipments ors WHERE o.customer_id=c.customer_id AND o.id=ors.order_id AND o.shipping_status='shipped' AND c.admin_id="+str(admin_id)+" AND ors.ship_date >= "+str(from_time)+" AND ors.ship_date <"+str(to_time)
		# cursor = connection.cursor()
		# cursor.execute(query)
		# res = cursor.fetchall()
		# for i in res:
		# 	print i
	
	#红人秀更新
	elif request.POST.get('type') == 'update_celebrity_show':
		product_ids = CelebrityImages.objects.filter(is_show=1,type__in=[1,3]).order_by('-id').values_list('product_id').distinct()[0:1500]
		for p in product_ids:
			product = Product.objects.filter(id=int(p[0])).first()
			if product:
				visibility = product.visibility
				status = product.status
				if visibility != 1 or status != 1:
					c_image = CelebrityImages.objects.filter(product_id=int(p[0])).update(is_show=0)
		messages.success(request, u'更新成功！')
		return redirect('celebrity_export')

	celebrits = Celebrits.objects.filter(admin_id__gt=100).values_list('admin_id').distinct()
	admin_id = []
	for i in celebrits:
		admin_id.append(int(i[0]))
	admin_id = tuple(admin_id)
	admins = User.objects.filter(id__in=admin_id)
	data['admins'] = admins

	data['title'] = ''
	return render(request,'celebrity_export.html',data)

