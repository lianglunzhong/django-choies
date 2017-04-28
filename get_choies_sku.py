# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import time, datetime

from products.models import OldProduct
import requests

_url = "http://www.choies.com/api/itemlist?page=%s&limit=1000" 

for i in range(1, 100):
    url = _url % i
    print url
    r = requests.get(url=url)
    items = r.json()

    if not items:
        break

    skus = []

    for item in items:
        skus.append(item['sku'])

    print skus
    for sku in set(skus):
        OldProduct.objects.get_or_create(sku=sku)
