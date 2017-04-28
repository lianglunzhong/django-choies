# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,Productitem

products = Product.objects.all()
n = 0
for product in products:
    items = Productitem.objects.filter(product_id=product.id).all()
    if items:
        status = 0
        for item in items:
            if item.status:
                status = 1
        if status:
            n = n + 1
            Product.objects.filter(id=product.id).update(status=1)
        else:
            Product.objects.filter(id=product.id).update(status=0)
print n