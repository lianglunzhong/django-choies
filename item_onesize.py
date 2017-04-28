# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import  Productitem
# from django.db.models import Sum,Count
from django.db import connection
sql = 'SELECT count(*),product_id FROM `products_productitem` GROUP BY product_id;'
# proitem = Productitem.objects.values('product_id','id').annotate(Count('product_id'))
cursor = connection.cursor()
cursor.execute(sql)
proitem = cursor.fetchall()
# print proitem
n = 0
for pro in proitem:
    # print pro
    if pro[0]>1:
        # print pro
        result = Productitem.objects.filter(product_id=pro[1]).values_list('id','attribute')
        for res in result:
            # print res
            if res[1]=='one size'or res[1]=='ONE SIZE':
                # print res
                n = n+1
                Productitem.objects.filter(id=res[0]).update(status=0)
print n