# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,Productitem,ProductFilter
from django.db import connection, transaction
# from django.core.cache import cache
import phpserialize
import memcache
def memcache_product(self):
    cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
    # 查询数据
    cursor = connection.cursor()
    query = 'select * from products_product where id = ' + str(self.id)
    cursor.execute(query)
    # 数据字段整合
    col_names = [desc[0] for desc in cursor.description]
    res = cursor.fetchone()
    data = dict(zip(col_names, res))
    # product attribute
    items = Productitem.objects.filter(product_id=self.id).values('status', 'attribute', 'stock')
    # print items
    if items:
        attribute = []
        stock = 0
        instock = 0
        status = 0
        for item in items:
            # attribute
            if item['attribute']:
                attribute.append(item['attribute'])
            # stock
            # if item['stock']:
            #     if item['stock']>0 or item['stock'] ==0:
            #         stock=stock+1
            stock = item['stock']

            # instock
            # if item['stock']<0:
            #     instock = 1
            # else:
            #     if item['stock']>0:
            #         instock = 1
            if item['stock'] > 0:
                instock = instock + 1

            # status
            if item['status'] == 1:
                status = status + 1
        attributes = {'Size': attribute}
        # if stock>0:
        #     stock = -1
        # else:
        #     stock = -99
        data['attributes'] = attributes
        data['instock'] = instock
        data['stock'] = stock
        data['status'] = status
    # product filter
    filters = ProductFilter.objects.filter(product_id=self.id).all()
    if filters:
        filter_str = ''
        for filter in filters:
            filter_str = filter_str + str(filter) + ';'
            # print filter_str
        data['filter_attributes'] = filter_str.strip(';')
    # 序列化
    product = phpserialize.dumps(data)
    # print '----',product
    # 设置缓存
    name = 'productcache1' + str(self.id)
    cache.set(name, product, 3600)
products = Product.objects.filter(visibility=1).all()
n = 0
for product in products:
    items = Productitem.objects.filter(product_id=product.id,status=1).count()
    if items ==0:
        # print items
        # print product.id,product.visibility
        # print '---'
        Product.objects.filter(id=product.id).update(visibility=0)
        pro = Product.objects.filter(id=product.id).first()
        # product.visibility = 0
        # product.save()
        # print pro.visibility
        # print '+++++++'
        memcache_product(product)
        n = n + 1
        print n