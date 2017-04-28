# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import time, datetime

from products.models import OldProduct, Product, ProductAttribute, Category
import requests

_url = "http://www.choies.com/api/item?sku=%s" 


for oldproduct in OldProduct.objects.filter(status=True):
    url = _url % oldproduct.sku
    
    r = requests.get(url=url)
    print url
    
    try:
        _products = r.json()
    except:
        oldproduct.status = False
        oldproduct.save()
        continue
    
    try:
        sku = _products[0]['sku']
    except:
        continue
    
    name = _products[0]['name']
    
    try:
        product = Product.objects.get(sku=sku)
    except:
        product = Product()
        product.sku = sku
    
    product.title = _products[0]['name']
    product.price = float(_products[0]['price'])
    product.attributes = _products[0]['image_url']
    
    category, _a = Category.objects.get_or_create(title=_products[0]['set'])
    
    product.category = category
    
    product.save()
    
    color = []
    size = []
    
    for _product in _products:
        try:
            size.append(_product['size'])
        except:
            pass
    
        try:
            color.append(_product['color'])
        except:
            pass
    
    if color:
        productattribute,_a = ProductAttribute.objects.get_or_create(name='color', product=product)
        productattribute.options = ','.join(color)
        productattribute.save()
    
    if size:
        productattribute,_a = ProductAttribute.objects.get_or_create(name='size', product=product)
        productattribute.options = ','.join(size)
        productattribute.save()
    
    oldproduct.status = False
    oldproduct.save()
    print _product
    
