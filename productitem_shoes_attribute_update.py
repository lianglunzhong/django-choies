# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Productitem

products = Productitem.objects.all()
n=0
for product in products:
    item_attribute = ''
    item_attribute = product.attribute
    #print '---', item_attribute
    item_attribute = str(item_attribute).split('/',1)

    item_first = item_attribute[0]
    #print item_first
    data = ''
    if item_first == 'US3':
        data = 'US4/UK1.5-UK2/EUR34/22cm'
    elif item_first == 'US4':
        data = 'US4/UK2-UK2.5/EUR35/22.5cm'
    elif item_first == 'US5':
        data = 'US5/UK3-UK3.5/EUR36/23cm'
    elif item_first == 'US6':
        data = 'US6/UK4-UK4.5/EUR37/23.5cm'
    elif item_first == 'US7':
        data = 'US7/UK5-UK5.5/EUR38/24cm'
    elif item_first == 'US8':
        data = 'US8/UK6-UK6.5/EUR39/24.5cm'
    elif item_first == 'US9':
        data = 'US9/UK7-UK7.5/EUR40/25cm'
    elif item_first == 'US10':
        data = 'US10/UK8-UK8.5/EUR41/25.5cm'
    elif item_first == 'US11':
        data = 'US11/UK9-UK9.5/EUR42/26cm'
    elif item_first == 'US12':
        data = 'US12/UK10-UK10.5/EUR43/26.5cm'
    elif item_first == 'US13':
        data = 'US13/UK11-UK11.5/EUR44/27cm'
    elif item_first == 'US14':
        data = 'US14/UK12-UK12.5/EUR45/27.5cm'
    if data:
        res = Productitem.objects.filter(id=product.id).update(attribute=data)
        if res:
            n=n+1
            print product.id
print 'update:',n