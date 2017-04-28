# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from django.db import connection, transaction
from products.models import Product,  Filter, CategorySorts, ProductFilter


'''
products_categorysorts表

'''
#查看索引
sql = "SHOW INDEX FROM products_categorysorts"
cursor = connection.cursor()
cursor.execute(sql)
results = cursor.fetchall()
#需要新添加的索引名称（字段）
categorysorts_attributes = 0
for res in results:
	#判断原来的索引中是否包含需要新添加的索引名称，避免报错脚本终止运行
	if 'categorysorts_attributes' in res:
		categorysorts_attributes = 1
#如果原来的索引中不包含需要新添加的索引名称，则新建索引
if not categorysorts_attributes:
	sql = "ALTER TABLE `products_categorysorts` ADD FULLTEXT INDEX `categorysorts_attributes` (`attributes`) "
	cursor = connection.cursor()
	cursor.execute(sql)

# products = Product.objects.filter(id=26706)
products = Product.objects.all()

n=0
for product in products:
		filter_attributes = product.filter_attributes
		if filter_attributes:
			filter_attributes = filter_attributes.strip().split(";")

			filter_sqls = []
			for i in filter_attributes:
				i = '"'+i+'"'
				filter_sqls.append(i)
			filter_sql = ','.join(filter_sqls)
			filter_sql = "'" + filter_sql + "'"
			
			query = "SELECT DISTINCT sort, attributes FROM products_categorysorts WHERE MATCH (attributes) AGAINST ("+filter_sql+" IN BOOLEAN MODE) ORDER BY sort"

			cursor = connection.cursor()
			cursor.execute(query)   #需要手动给products_categorysorts的attributes添加fulltext索引
			sorts = cursor.fetchall()

			for sort in sorts:
				attributes = sort[1].lower().split(',')
				attr = ''
				for filter_attribute in filter_attributes:
					filter_attribute = filter_attribute.lower()
					if filter_attribute in attributes:
						attr = filter_attribute
						break
				filter_option = ''
				filter_name = ''
				if attr:
					filter_option = attr
					filter_name = sort[0].upper()

				if filter_name and filter_option:
					query1, is_created1 = Filter.objects.get_or_create(name=filter_name,options=filter_option)
					# print str(query1.id) + '  products_filter'
					if query1:
						query2, is_created2 = ProductFilter.objects.get_or_create(options=filter_option,filter_id=query1.id,product_id=product.id)
						# print str(query2.id) + '  products_productfilter'
						n=n+1
print n










       





