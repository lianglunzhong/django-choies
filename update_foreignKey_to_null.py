# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product
#set
products = Product.objects.filter(set_id=0).all()
# print '----',products
n = 0
for product in products:
    n = n + 1
    Product.objects.filter(id=product.id).update(set_id=None)
print 'set:',n

#brand
products = Product.objects.filter(brand_id=0).all()
# print '----',products
n = 0
for product in products:
    n = n + 1
    Product.objects.filter(id=product.id).update(brand_id=None)
print'brand:', n

#admin
products = Product.objects.filter(admin_id=0).all()
# print '----',products
n = 0
for product in products:
    n = n + 1
    Product.objects.filter(id=product.id).update(admin_id=None)
print 'admin:',n

#offline_picker
products = Product.objects.filter(offline_picker_id=0).all()
# print '----',products
n = 0
for product in products:
    n = n + 1
    Product.objects.filter(id=product.id).update(offline_picker_id=None)
print 'offline_picker:',n
