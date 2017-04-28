# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Productitem,Stocks

product_id = Productitem.objects.values_list('product_id').all()
n=0
m=0
for p in  product_id:
    product = Stocks.objects.filter(product_id=p).all()
    if product:
        for item in product:
            print item.product_id
            if item:
                res = Productitem.objects.filter(product_id=item.product_id,attribute=item.attributes).update(stock=item.stocks,status=item.isdisplay)
                if res:
                    n = n+1
        m = m+1
print 'update:',n
print 'total:',m