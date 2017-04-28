# coding: utf-8
# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from django.db import connection

'''
同步数据前先运行此脚本

'''

'''
accounts_customers表

'''
#查看索引
sql = "SHOW INDEX FROM accounts_customers"
cursor = connection.cursor()
cursor.execute(sql)
results = cursor.fetchall()
#需要新添加的索引名称（字段）
customer_email = 0
customer_last_login_time = 0
customer_status_created = 0
for res in results:
	#判断原来的索引中是否包含需要新添加的索引名称，避免报错脚本终止运行
	if 'customer_email' in res:
		customer_email = 1
	if 'customer_last_login_time' in res:
		customer_last_login_time = 1
	if 'customer_status_created' in res:
		customer_status_created = 1
#如果原来的索引中不包含需要新添加的索引名称，则新建索引
if not customer_email:
	sql = "ALTER TABLE `accounts_customers` ADD UNIQUE INDEX `customer_email` (`email`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not customer_last_login_time:
	sql = "ALTER TABLE `accounts_customers` ADD INDEX `customer_last_login_time` (`last_login_time`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not customer_status_created:
	sql = "ALTER TABLE `accounts_customers` ADD INDEX `customer_status_created` (`status`, `created`)  "
	cursor = connection.cursor()
	cursor.execute(sql)


'''
products_product表

'''
#查看索引
sql = "SHOW INDEX FROM products_product"
cursor = connection.cursor()
cursor.execute(sql)
results = cursor.fetchall()
#需要新添加的索引名称（字段）,产品表sku后台model中添加了唯一索引，第一次做版本时自动添加索引
product_display_date = 0
product_status = 0
product_visibility = 0
product_name_sku_des_key = 0
for res in results:
	#判断原来的索引中是否包含需要新添加的索引名称，避免报错脚本终止运行
	if 'product_display_date' in res:
		product_display_date = 1
	if 'product_status' in res:
		product_status = 1
	if 'product_visibility' in res:
		product_visibility = 1
	if 'product_name_sku_des_key' in res:
		product_name_sku_des_key = 1
#如果原来的索引中不包含需要新添加的索引名称，则新建索引
if not product_display_date:
	sql = "ALTER TABLE `products_product` ADD INDEX `product_display_date` (`display_date`)  "
	cursor = connection.cursor()
	cursor.execute(sql)
if not product_status:
	sql = "ALTER TABLE `products_product` ADD INDEX `product_status` (`status`)  "
	cursor = connection.cursor()
	cursor.execute(sql)
if not product_visibility:
	sql = "ALTER TABLE `products_product` ADD INDEX `product_visibility` (`visibility`)  "
	cursor = connection.cursor()
	cursor.execute(sql)
if not product_name_sku_des_key:
	sql = "ALTER TABLE `products_product` ADD FULLTEXT INDEX `product_name_sku_des_key` (`name`, `sku`, `description`, `keywords`)"
	cursor = connection.cursor()
	cursor.execute(sql)


'''
orders_order表

'''
#查看索引
sql = "SHOW INDEX FROM orders_order"
cursor = connection.cursor()
cursor.execute(sql)
results = cursor.fetchall()
#需要新添加的索引名称（字段）
order_erp_fee_line_id = 0
order_is_active = 0
order_created = 0
order_shipping_date = 0
order_shipping_country = 0
for res in results:
	#判断原来的索引中是否包含需要新添加的索引名称，避免报错脚本终止运行
	if 'order_erp_fee_line_id' in res:
		order_erp_fee_line_id = 1
	if 'order_is_active' in res:
		order_is_active = 1
	if 'order_created' in res:
		order_created = 1
	if 'order_shipping_date' in res:
		order_shipping_date = 1
	if 'order_shipping_country' in res:
		order_shipping_country = 1
#如果原来的索引中不包含需要新添加的索引名称，则新建索引
if not order_erp_fee_line_id:
	sql = "ALTER TABLE `orders_order` ADD INDEX `order_erp_fee_line_id` (`erp_fee_line_id`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not order_is_active:
	sql = "ALTER TABLE `orders_order` ADD INDEX `order_is_active` (`is_active`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not order_created:
	sql = "ALTER TABLE `orders_order` ADD INDEX `order_created` (`created`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not order_shipping_date:
	sql = "ALTER TABLE `orders_order` ADD INDEX `order_shipping_date` (`shipping_date`) "
	cursor = connection.cursor()
	cursor.execute(sql)
if not order_shipping_country:
	sql = "ALTER TABLE `orders_order` ADD INDEX `order_shipping_country` (`shipping_country`) "
	cursor = connection.cursor()
	cursor.execute(sql)

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