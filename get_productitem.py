# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,Productitem
import phpserialize

#products = Product.objects.filter(id=19033).all()
products = Product.objects.all()
n = 0
for product in products:

    if product.attributes:
        try:
            attributes = phpserialize.loads(product.attributes)
        except Exception, e:
            pass
    if attributes:
        size = attributes.keys()

        sizes = attributes.values()
        sizes = sizes[0]

        options = sizes.values()
        #option = ','.join(option)
        if product.stock == -1:
            stock = 0
        else:
            stock = product.stock
        for option in  options:
            query, is_created = Productitem.objects.get_or_create(attribute=option,stock=stock, product_id=product.id)
            n = n+1
            print query.id
print 'insert:',n