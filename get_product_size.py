# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,  ProductAttribute
import phpserialize
from core.views import write_csv

products = Product.objects.all().order_by('-id')
# products = Product.objects.filter(id=71910)

for product in products:
	if product.attributes:
		try:
			attributes = phpserialize.loads(product.attributes)
		except Exception,e:
			pass

		if attributes:
			sizes = attributes.values()
			sizes = sizes[0]

			psize = ''
			for size in sizes.values():
				psize += str(size)+"#"

			#去除最后一个#号
			if psize:
				psize = psize[0:len(psize)-1]

				print u"%s,%s"%(product.sku,psize)







