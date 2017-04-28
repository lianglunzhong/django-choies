# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,  ProductAttribute
import phpserialize

products = Product.objects.all()
# products = Product.objects.filter(id=11918)
for product in products:
	if product.attributes:
		try:
			attributes = phpserialize.loads(product.attributes)
		except Exception,e:
			pass 
		if attributes:
			size = attributes.keys()
			name = str(size[0])

			sizes = attributes.values()
			sizes = sizes[0]

			option = sizes.values()
			option = ','.join(option)

			query, is_created = ProductAttribute.objects.get_or_create(name=name,options=option,product_id=product.id)
			print query.id
       





