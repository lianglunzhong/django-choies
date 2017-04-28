# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import time, datetime

from products.models import Product, Category
import requests

for product in Product.objects.all():
    print product
   #product.es_index()
    product.update_variants()
   
