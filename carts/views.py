#-*- coding: utf-8 -*-
from django.shortcuts import render
from carts.models import Spromotions,Promotions,Coupons
from products.models import Product,Filter,Category,CategoryProduct,Productitem
from carts.models import CustomerCoupons
from accounts.models import Customers
import datetime,time
import memcache
import csv
import StringIO
from core.views import eparse,nowtime,write_csv,time_stamp,time_stamp2,time_stamp6
import phpserialize
from django.contrib import messages
from dal import autocomplete
from celebrities.models import Celebrits
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.shortcuts import get_object_or_404, redirect
# from django.core.cache import cache
from django.conf import settings
from orders.models import Order,OrderItem
import urllib
import urllib2
import demjson
import thread 

@login_required
def index(request):
    context = {}
    return render(request, 'cart_index.html', context)

class ProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Product.objects.none()

        qs = Product.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs

class CelebritsAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Celebrits.objects.none()

        qs = Celebrits.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs

class FilterAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Filter.objects.none()

        qs = Filter.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs

class CategoryAllAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Category.objects.none()

        qs = Category.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs
class ProductitemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Productitem.objects.none()

        qs = Productitem.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs

class CustomerCouponsAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Customers.objects.none()

        qs = Customers.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q)

        return qs

@login_required
def add(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def sub(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def delete(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def shipping(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def handle(request):
    context = {}
    return render(request, 'cart_handle.html', context)

@login_required
def add_spromotion_memcache(request):
    context = {}
    #spromotions 特殊产品促销
    expired_time = int(time.time())
    spromotions = Spromotions.objects.filter(expired__gte=expired_time).\
    values('id', 'product_id', 'price', 'type', 'created', 'expired')
    for obj in spromotions:
        if int(obj['price']) > 0:
            cache_one = {}
            cache_one['price'] = obj['price']
            cache_one['created'] = time.mktime(obj['created'].timetuple())
            cache_one['expired'] = time.mktime(obj['expired'].timetuple())

            cache_key ='spromotion_' + str(obj['product_id'])
            cache = memcache.Client([settings.MEMCACHE_URL])
            cache_data = {}
            cache_data[obj['type']] = cache_one
            cache_data =  phpserialize.dumps(cache_data)
            cache.set(cache_key,cache_data)
    #promotions 传统促销
    cache_key = 'promotions_product'
    time_now = int(time.time())
    promotions = Promotions.objects.filter(from_date__lte=time_now,to_date__gte=time_now,is_active=1).values(
    'id','name','brief', 'filter','actions','args','is_active','is_view', 'from_date', 'to_date','order',
    'deleted','admin_id','price_lower','price_upper')
    i = 0

    cache_data = {}
    for obj in promotions:
        if obj:
            cache_one = obj
            cache_one['from_date'] = time.mktime(obj['from_date'].timetuple())
            cache_one['to_date'] = time.mktime(obj['to_date'].timetuple())
            # cache_one['created'] = time.mktime(obj['created'].timetuple())
            # cache_one['updated'] = time.mktime(obj['updated'].timetuple())
            cache_data[i] = cache_one
            i = i+1
    # print '---',cache_data
    data =  phpserialize.dumps(cache_data)
    cache = memcache.Client([settings.MEMCACHE_URL])
    cache.set(cache_key,data,6000)
    messages.success(request, u'缓存设置成功')
    return render(request, 'cart_handle.html', context)

@login_required
def add_spromotion_memcache_data(request):
    context = {}
    if request.POST.get('type') == 'sku_memcache_add':
        print '------'
        print 111
        skus = request.POST.get('skus', '').strip().split('\r\n')
        print skus
        if skus[0]:
            ids = Product.objects.filter(sku__in=skus, deleted=0).values_list('id')
            expired_time = int(time.time())
            for i in ids:
                spromotions = Spromotions.objects.filter(expired__gte=expired_time, product_id=i[0]). \
                    values('id', 'product_id', 'price', 'type', 'created', 'expired')

                for obj in spromotions:
                    if int(obj['price']) > 0:
                        cache_one = {}
                        cache_one['price'] = obj['price']
                        cache_one['created'] = time.mktime(obj['created'].timetuple())
                        cache_one['expired'] = time.mktime(obj['expired'].timetuple())

                        cache_key = 'spromotion_' + str(i[0])
                        cache = memcache.Client([settings.MEMCACHE_URL])
                        cache_data = {}
                        cache_data[obj['type']] = cache_one
                        cache_data = phpserialize.dumps(cache_data)
                        print cache.set(cache_key, cache_data)
                messages.success(request, u'缓存设置成功')

        else:
            messages.error(request, u'sku不能为空')

    elif request.POST.get('type') == 'do_promotion_insert':
        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['file'].read()))
        header = next(reader)
        std_header = [
            "SKU","Price","Catalog","Expired Time","Type"
        ]
        field_header = [
            "sku", 'price', 'catalog',"expired", "type"
        ]

        # 由于bom头的问题, 就不比较第一列的header了
        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('handle')

        types = {}
        types['vip'] = 0
        types['daily'] = 1
        types['cost']= 2
        types['outlet'] = 3
        types['special'] = 4
        types['activity'] = 5
        types['flash_sale'] = 6
        types['top_seller'] = 7
        types['bomb'] = -1

        for i, row in enumerate(reader, 2):
            res = dict(zip(field_header, row))

            order_dict = {}
            pro_id = Product.objects.filter(sku=res['sku']).values('id','price')
            order_dict['product_id'] = int(pro_id[0]['id'])
            order_dict['price'] = res['price']
            if(float(pro_id[0]['price']) < float(order_dict['price'])):
                pass
            else:
                order_dict['catalog'] = ''
                order_dict['price'] = float(res['price'])
                times = time_stamp6(res['expired'])
                order_dict['expired'] = times
                res['type'] = res['type'].lower()
                if res['type'] in types.keys():
                    order_dict['type'] = types[res['type']] or 1

                order_dict['admin'] = int(request.user.id)
                if order_dict['type'] == 0:
                    has = Spromotions.objects.filter(type=0,product_id=order_dict['product_id']).first()
                else:
                    has = Spromotions.objects.filter(product_id=order_dict['product_id']).exclude(type=0).first()

                if not has:
                    c = Spromotions.objects.create(price=order_dict['price'],
                                          type=order_dict['type'],
                                          # expired=order_dict['expired'],
                                          admin_id=order_dict['admin'],
                                          product_id=order_dict['product_id']
                                         )
                    if c:
                        sql = "UPDATE carts_spromotions SET expired="+str(order_dict['expired'])+" WHERE id="+str(c.id)
                        cursor = connection.cursor()
                        cursor.execute(sql)

                    cache_key ='spromotion_' + str(order_dict['product_id'])
                    cache= memcache.Client([settings.MEMCACHE_URL])
                    cache_data = {}
                    cache_data[order_dict['type']] = order_dict
                    cache_data =  phpserialize.dumps(cache_data)
                    print cache.set(cache_key,cache_data)
                else:
                    promo = Spromotions.objects.get(product_id=order_dict['product_id'])
                    promo.price=order_dict['price']
                    promo.type=order_dict['type']
                    # promo.expired=order_dict['expired']
                    promo.admin_id=order_dict['admin']
                    promo.product_id=order_dict['product_id']
                    c = promo.save()
                    if promo:
                        sql = "UPDATE carts_spromotions SET expired="+str(order_dict['expired'])+" WHERE id="+str(promo.id)
                        cursor = connection.cursor()
                        cursor.execute(sql)

                    cache_key ='spromotion_' + str(order_dict['product_id'])
                    cache= memcache.Client([settings.MEMCACHE_URL])
                    cache_data = {}
                    cache_data[order_dict['type']] = order_dict
                    cache_data =  phpserialize.dumps(cache_data)
                    print cache.set(cache_key,cache_data)
        messages.success(request, u'缓存设置成功')
    elif request.POST.get('type') == 'export_special_expired':
        response, writer = write_csv("special_expired_product")
        writer.writerow(["sku", "Orig_Price","Sale_Price","Created_Time", "Expired_Time", "Admin"])
        t = nowtime()
        queryset=Spromotions.objects.filter(expired__lt=t,product__status=1,product__visibility=1)
        for query in queryset:
            row = [
                str(query.product.sku),
                str(query.product.price),
                str(query.price),
                str(query.created),
                str(query.expired),
                str(),
            ]
            writer.writerow(row)
        return response
    
    #新品促销分类产品关联
    elif request.POST.get('type') == 'new_relate':
        #关联类型
        relate_type = request.POST.get('new_relate_selete','')
        if relate_type == 'one_week':
            relate_type = 1
        else:
            relate_type = 2
        #调用前台接口
        relate_type = demjson.encode(relate_type)

        url = settings.BASE_URL+'adminapi/new_relate'
        # url = 'http://local.oldchoies.com/adminapi/new_relate'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req,urllib.urlencode({'relate_type':relate_type}))
       

        '''
        now = time.time()
        nowtime = now - (now % 86400) + time.timezone
        #关联一周数据操作
        if relate_type == 'one_week':
            #前一周时间
            lasttime = int(nowtime) - 7*86400
        else:
            #前两周时间
            lasttime = int(nowtime) - 14*86400
        #新品分类
        category = Category.objects.filter(link='new-product').first()
        #当前一周内上新的产品
        products = Product.objects.filter(visibility=1,display_date__gte=lasttime,display_date__lt=nowtime).all()
        #把该时间段内的新品关联到新品分类中
        for product in products:
            #更新产品分类关联表（手动创建的表）
            query, is_created = CategoryProduct.objects.get_or_create(category_id=category.id,product_id=product.id,deleted=0)
        '''

        messages.success(request, u"Relate "+relate_type+" new product Success!")


    #新品促销分类产品删除
    elif request.POST.get('type') == 'new_delete':
        category = Category.objects.filter(link='new-product').first()
        if category:
            #删除产品分类关联表（手动创建的表）
            result1 = CategoryProduct.objects.filter(category_id=category.id).delete()

            if result1:
                messages.success(request,u'Delete new product Success!')
                return redirect('cart_promition_data')
            else:
               messages.error(request ,u'Delete new product Failed!')
            return redirect('cart_promition_data') 
        else:
            messages.error(request ,u'无新品促销分类')
            return redirect('cart_promition_data')

    elif request.POST.get('type') == 'export_coupons_order':
        data = request.POST.get('coupons')
        print '---',data
        coupon = Coupons.objects.filter(code=data).first()
        if coupon:
            orders = Order.objects.filter(coupon_code=coupon.code).all()
            if orders:
                response, writer = write_csv("coupons_orders")
                writer.writerow(["Ordernum", "Amount", "Currency", "Created", "Payment_status"])
                for order in orders:
                    row = [
                        str(order.ordernum),
                        str(order.amount),
                        str(order.currency),
                        str(order.created),
                        str(order.payment_status),
                    ]
                    writer.writerow(row)
                return response
            else:
                messages.error(request,u'折扣号尚未使用')
        else:
            messages.error(request,u'折扣号不存在')
    else:
        context = {}
    return render(request, 'cart_handle.html', context)


def eparse(value, offset=None):
    '''将str类型的时间转化成: 含时区的datetime
    easy parse的简称 eparse

    value: str
    offset: str '+08:00' value是东八区时间, 但字符串中没有时区信息
                '+00:00' value是UTC时间, 但字符串中没有时区信息
    如果传的是date类型, 需要自己补足时分秒
            offset=" 00:00:00+08:00"

    有时区的字符串: '2016-01-01 12:59:12 +08:00'
    无时区的字符串: '2016-01-01 12:59:12'  这种类型需要手动传递后缀'+00:00'或对应时区
    '''
    try:
        if offset:
            value += offset
        t = parse(value)
    except Exception, e:
        t = None
    return t
