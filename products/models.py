# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.db import models
from mptt.models import MPTTModel
from django.contrib import messages
import datetime,time
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
import uuid
from uuslug import slugify
import hashlib
import os
import itertools
from elasticsearch import Elasticsearch
from django.core.urlresolvers import reverse
from django_unixdatetimefield import UnixDateTimeField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from celebrities.models import Celebrits
import carts
from core.views import eparse,nowtime,pp
import phpserialize
from django.db import connection, transaction
from django.conf import settings
import urllib
import urllib2
import json
# import sys, os
# reload(sys)
# sys.setdefaultencoding('utf-8')
import memcache
# from django.core.cache import cache


class OldProduct(models.Model):

    sku = models.CharField(max_length=100)
    status = models.BooleanField(default=True)

    def __unicode__(self):
        return self.sku


class Filter(models.Model):

    TYPE = (
            (0, u'Mulit Select'),
            (1, u'One Select'),
            (2, u'Input'),
        )

    type = models.IntegerField(choices=TYPE, default=0)
    name = models.CharField(max_length=100)
    options = models.TextField(blank=True, default="")
    required = models.BooleanField(default=False)

    def __unicode__(self):
        return self.options

    class Meta:
        verbose_name = u'产品过滤'
        verbose_name_plural = u'产品过滤'

class Collection(MPTTModel):
    name = models.CharField(max_length=100, verbose_name=u"分类名称")
    code = models.CharField(max_length=2, help_text=u"00-ZZ")
    parent = models.ForeignKey("self", blank=True, null=True, related_name="children", verbose_name=u"父级分类")
    brief = models.TextField(blank=True, verbose_name=u"分类简介")
    status = models.BooleanField(default=True)
    #filters = models.ManyToManyField(Filter, blank=True)

    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

   #class Meta:
   #    verbose_name = u'产品分类'
   #    verbose_name_plural = u'产品分类'

    def __unicode__(self):
        # return "%03d.%s" % (self.id, self.name)
        return self.name

    @property
    def link(self):
        return slugify(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('collection', (), {'id':self.id, "link":self.link,})


def get_image_upload_path(instance, filename):
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    #name = time.strftime('%y-%m/%d',time.localtime(time.time()))
    name = str(uuid.uuid4())
    return os.path.join('img', name[0:3], name[3:]+ext)

def get_product_image_upload_path(instance, filename):
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    image_id = instance.id
    if image_id:
        name = str(instance.id)+ext
    else:
        image = ProductImage.objects.all().order_by('-id').first()
        name = str(int(image.id)+int(1))+ext
    return '%s/%s' %('pimages/',name)

def get_celebrity_image_upload_path(instance, filename):
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    name = fn+ext
    return '%s/%s' %('simages/',name)

def get_category_image_upload_path(instance, filename):
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    name = fn+ext
    return '%s/%s' %('simages/',name)



class Category(MPTTModel):
    VISIBILITY = (
            (1,u"可见"),
            (0,u"不可见"),
        )

    ORDERBY = (
            (1,u"新增时间"),
            (2,u"购买次数"),
            (3,u"名称"),
            (4,u"价格"),
        )

    DESC = (
            (0,u"倒序"),
            (1,u"升序"),
        )

    STEREOTYPED = (
            (1,u"显示"),
            (0,u"隐藏"),
        )

    IS_BRAND = ON_MENU =(
            (1,u"是"),
            (0,u"否"),
        )

    name = models.CharField(max_length=255,default='', blank=True,null=True, verbose_name=u"分类名称")
    link = models.CharField(max_length=255, default='', verbose_name=u"URL")
    #code = models.CharField(max_length=2, help_text=u"00-ZZ")
    parent = models.ForeignKey("self", blank=True, null=True,related_name="children", verbose_name=u"父级分类")
    # status = models.BooleanField(default=True)
    filters = models.ManyToManyField(Filter, blank=True)
    
    orderby = models.CharField(max_length=100, default='',blank=True,null=True, verbose_name=u"Products order by")
    desc = models.IntegerField(choices=DESC, default=1, verbose_name=u"升/倒序")
    visibility = models.IntegerField(choices=VISIBILITY, default=1, verbose_name=u"是否可见")
    on_menu = models.IntegerField(choices=ON_MENU, default=1, verbose_name=u"Listed on menu")
    stereotyped = models.IntegerField(choices=STEREOTYPED, default=1, verbose_name=u"Stereotyped modules")
    # site_id = models.BooleanField(default=0)
    
    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False,blank=True, verbose_name=u"是否已删除")

    template = models.CharField(max_length=100, blank=True, verbose_name=u"分类模板")
    brief = models.TextField(blank=True, verbose_name=u"分类简介")
    description = models.TextField(blank=True,default='',null=True, verbose_name=u"分类描述")
    hot_catalog = models.TextField(blank=True,default='',null=True, verbose_name=u"hot catalog & link", help_text=u"格式：dresses,dresses-c-92")
    #position = models.IntegerField(default=0, verbose_name=u"排序")
    is_brand = models.IntegerField(choices=IS_BRAND, default=0, verbose_name=u"Is Brand")
    price_ranges = models.CharField(max_length=100, blank=True, verbose_name=u"Price Ranges", help_text=u"e.x: '5,7' means '(0,5],(5,7]' ") 

    meta_title = models.CharField(blank=True, max_length=100, default='', verbose_name=u"SEO标题")
    meta_keywords = models.TextField(blank=True,null=True,default='', verbose_name=u"SEO关键字")
    meta_description = models.TextField(blank=True,null=True, verbose_name=u"SEO描述")

    #max_count = models.IntegerField(default=0, help_text=u"分类中展示的最多产品数，影响前台分页的页数，为0则不限制")
    recommended_products = models.CharField(max_length=100, blank=True,default='', verbose_name=u"推荐产品sku", help_text="用','隔开，如：'CAAAFT2,BD000KTV,BD000KTX' ")
    image_src = models.ImageField(upload_to=get_category_image_upload_path, blank=True,default='',  verbose_name=u"图片地址")
    image_link = models.CharField(max_length=100, blank=True,default='', verbose_name=u"图片链接")
    image_alt = models.CharField(max_length=100, blank=True,default='', verbose_name=u"图片文本", help_text=u"图片无法显示时将用该文字代替")
    image_map = models.TextField(blank=True,default='', verbose_name=u"Image Map")
    pimage_src = models.ImageField(upload_to=get_category_image_upload_path,blank=True,default='', verbose_name=u"手机图片地址")
    position = models.IntegerField(default=0, verbose_name=u"排序")
    is_filter = models.IntegerField(default=0, verbose_name=u"是否有排序规则") 
    pimage_map = models.TextField(blank=True, default='', verbose_name=u"手机版Image Map")

    class Meta:
        verbose_name = u'分类'
        verbose_name_plural = u'分类'

    def __unicode__(self):
        # return "%03d.%s" % (self.id, self.name)
        return self.name

    @property
    def category_link(self):
        return slugify(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('category', (), {'id':self.id, "link":self.category_link,})

    """分类图片保存时去掉simages/,只保留图片名称"""
    def change_category_imagename(self,request):
        category = Category.objects.filter(id=self.id).first()
        if category:
            image_src = category.image_src
            pimage_src = category.pimage_src
            if image_src:
                image_src = str(image_src)
                if image_src.find('simages/') != -1:
                    index = image_src.find('simages/')+8
                    name = image_src[index:]
                    query = Category.objects.filter(id=self.id).update(image_src=name)
            if pimage_src:
                pimage_src = str(pimage_src)
                if pimage_src.find('simages/') != -1:
                    index = pimage_src.find('simages/')+8
                    name = pimage_src[index:]
                    query = Category.objects.filter(id=self.id).update(pimage_src=name)


    def es_index(self):
        es = Elasticsearch()
        _body= {
                "title": self.name,
                "brief": self.sku,
                "id": self.id,
                "url": self.get_absolute_url(),
        }
        res = es.index(index= settings.ES_INDEX, doc_type='category', id=self.id, body=_body)
        return res

    def es_delete(self):
        es = Elasticsearch()
        res = es.delete(index=settings.ES_INDEX, doc_type='category', id=self.id, ignore=[400, 404])
        return res

    # def cate_basic_save(self, request):
    #     if request.POST.get('type', '') == 'cate_basic_save':
    #         category_links = request.POST.get('category_links', '').strip().split('\r\n')
    #         print category_links
    #         category_linkarr = Category.objects.filter(category_link__in=category_links,deleted=0).values_list('id')

class CategorySorts(models.Model):

    category = models.ForeignKey(Category, verbose_name=u"分类名称")
    sort = models.CharField(default='',max_length=40,verbose_name="SKU")
    attributes = models.TextField(blank=True, null=True,default=False, verbose_name=u"属性")
    # site_id = models.BooleanField(default=1)

    def __unicode__(self):
        return self.sort

class Product(models.Model):

    STATUS = (
            (1, u'上架'),
            (0, u'下架'),
        )

    VISIBILITY = (
            (1, u'可见'),
            (0, u'不可见'),
        )

    ERP_ITEM = (
            (0,u'未抓单'),
            (1,u'已抓单'),
        )

    TYPE= (
            (0,u'基本产品'),
            (1,u'配置产品'),
            (2,u'打包产品'),
            (3,u'简单配置产品'),
        )

    STOCK = (
            (-99,u'不限制'),
            (-1,u'限制'),
            (0,u'不可售'),
        )
    SOURCE = (
            ('采购','采购'),
            ('做货','做货'),
            ('库存限制销售','库存限制销售'),
    )

    name = models.CharField(max_length=300,db_index=True, verbose_name=u"产品名称")
    link = models.CharField(max_length=300,blank=True, default='',verbose_name=u'URL')
    category = models.ManyToManyField(Category,verbose_name=u"分类名称", help_text=u"更改产品分类后，请立即保存",through ='CategoryProduct')
    sku=models.CharField(max_length=200,unique=True,verbose_name="SKU",)
    price = models.FloatField(default=0.0, verbose_name=u"本站价格")
    market_price = models.FloatField(default=0.0, verbose_name=u"市场价格")

    status = models.IntegerField(choices=STATUS, default=1,db_index=True, verbose_name=u"状态")
    description = models.TextField(blank=True, null=True, default='', verbose_name=u"产品描述")
    attributes = models.TextField(blank=True, null=True, default='')
    weight = models.FloatField(default=0.0, help_text=u"基本单位为KG 千克", verbose_name=u"产品重量")

    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=0, blank=True, verbose_name=u"是否已删除")

    #new add field
    store = models.CharField(max_length=100,default='',blank=True,null=True,verbose_name='Store')
    keywords = models.TextField(default='',blank=True,null=True,verbose_name='Keywords')
    erp_item_id = models.BooleanField(choices=ERP_ITEM, default=0)
    # site_id = models.BooleanField(default=1)
    cost = models.FloatField(default=0.0, verbose_name=u"USD成本")
    total_cost = models.FloatField(default=0.0, verbose_name=u"RMB成本")
    stock = models.IntegerField(choices=STOCK,default=-99,verbose_name=u'库存状态')
    brief = models.TextField(blank=True, null=True, default='', verbose_name=u"产品详情")
    display_date = UnixDateTimeField(blank=True, null=True,db_index=True, verbose_name=u"上新时间")
    meta_title = models.CharField(blank=True,max_length=100, default='',verbose_name=u"SEO标题")
    meta_keywords = models.CharField(blank=True,max_length=100,default='', verbose_name=u"SEO关键字")
    meta_description = models.CharField(blank=True,max_length=300,default='', verbose_name=u"SEO描述")
    hits = models.IntegerField(default=0, verbose_name=u"购买次数")
    set = models.ForeignKey('products.Set',blank=True, null=True, verbose_name=u"品类", help_text=u"更改产品set后，请立即保存")
    type = models.IntegerField(choices=TYPE, default=3,verbose_name=u"产品类型")
    visibility = models.IntegerField(choices=VISIBILITY, default=1,db_index=True, verbose_name=u"是否可见")
    factory = models.CharField(blank=True,max_length=200,null=True, default='', verbose_name=u"供货商")
    attributes = models.TextField(blank=True, null=True, default='', verbose_name=u"属性")
    offline_factory = models.CharField(blank=True,max_length=200, default='', verbose_name=u"线下供货商")
    offline_sku = models.CharField(blank=True,max_length=50, default='', verbose_name=u"线下供货商SKU")
    taobao_url = models.CharField(blank=True,max_length=500,default='', verbose_name=u"淘宝url") 
    presell = UnixDateTimeField(blank=True, null=True,  verbose_name=u"预售到期时间")
    presell_message = models.CharField(blank=True,max_length=100,default='', verbose_name=u"预售文案")
    filter_attributes = models.TextField(blank=True, null=True, default='', verbose_name=u"过滤属性")
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin', related_name="admin_user")
    position = models.IntegerField(default=0, verbose_name=u"排序")
    source = models.CharField(choices=SOURCE,blank=True,max_length=100,default='采购', verbose_name=u"供货来源")
    offline_picker = models.ForeignKey(User,related_name=u'offline_picker', null=True, blank=True, verbose_name=u'选款人')
    extra_fee = models.FloatField(default=0.0, verbose_name=u"低单价产品加收运费")
    cn_name = models.CharField(blank=True,max_length=100,default='', verbose_name=u"产品名中文")
    brand = models.ForeignKey('products.Brands', blank=True, null=True, verbose_name=u'品牌') 
    configs = models.TextField(default='',blank=True,null=True,verbose_name='产品图片序列化数据保存')
    has_pick = models.IntegerField(default=0, verbose_name=u"可挑选")
    add_times = models.IntegerField(default=0)
    default_catalog = models.CharField(blank=True,max_length=10,default='', verbose_name=u"默认分类")
    _category_id = None

    class Meta:
        verbose_name = u'产品'
        verbose_name_plural = u'产品'
        # unique_together = ('name','sku','keywords')

    def es_index(self):
        #es = Elasticsearch()
        es = Elasticsearch(settings.ES_URL)
        # es = Elasticsearch("192.168.11.150:9200")
        # res = es.search(
        #     index='product_basic_new_',
        #     doc_type='product_',
        #     body={
        #       'query': {
        #         'match': {
        #           'id': self.id
        #         }
        #       }
        #     }
        # )

        tt = str(self.display_date)
        if tt == 'None':
            timeStamp = 0
        else:
            timeArray = time.strptime(tt, "%Y-%m-%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))

        _body= {
                "id": self.id,
                "name": self.name,
                "link": self.link,
                "sku": self.sku,
                "visibility": self.visibility,  
                "status": self.status,
                "description": self.description,
                "price": self.priceto(),
                "display_date": timeStamp,
                "hits": self.hits,
                "has_pick": self.has_pick,
                "filter_attributes": self.filter_attributes,
                "position": self.position,
                "attributes": '',
                "pro_price": self.price,
                "cover_image": self.cover_image(),
                "name_de": '',
                "description_de":self.description,
                "name_es": '',
                "description_es":self.description,
                "name_fr": '',
                "description_fr":self.description,
                "keywords": '',
        }


        if self.keywords:
            brand = self.brand_id
            keyword =  str(self.keywords) + str(brand)
            _body['keywords'] = keyword 

        _body['has_promotion'] = 0
        if _body['pro_price'] > _body['price']:
            _body['has_promotion'] = 1

        attr_value = self.attr()
        _body['attributes'] = attr_value['attributes']
        _body['size_value'] = attr_value['size_value'] 
        _body['color_value'] = attr_value['color_value'] 
        _body['default_catalog'] = attr_value['default_catalog']

        res = es.index(index= settings.ES_INDEX, doc_type='product_', id=self.id, body=_body)
        return res

    def es_delete(self):
        es = Elasticsearch()
        res = es.delete(index=settings.ES_INDEX, doc_type='product_', id=self.id, ignore=[400, 404])
        return res

    def es_search(self):
        es = Elasticsearch()
        es = Elasticsearch(settings.ES_URL)
        res = es.search(
            index=settings.ES_INDEX,
            doc_type='product_',
            body={
              'query': {
                'match': {
                  'id': self.id
                }
              }
            }
        )
        return ast.literal_eval(res)

    def es_update(self):
        es = Elasticsearch()
        res = es.search(index=settings.ES_INDEX, doc_type='product', id=self.id, doc=_body,ignore=[400, 404])
        return res

    @property
    def product_link(self):
        return slugify(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('product', (), {'id':self.id, "link":self.product_link,})

   #class Meta:
   #    verbose_name = u'产品'
   #    verbose_name_plural = u'产品'

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        # if self.category_id:
        #     self._category_id = self.category_id

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def update_variants(self):
        # print 'update variants'
        options = []
        for productattribute in self.productattribute_set.order_by('id'):
            _options = productattribute.get_options()
            if _options:
                options.append(_options) 

        keys=[]

        if len(options) > 1:
            for x in itertools.product(*_options):
                keys.append(str(self.id) + '_' + '_'.join([str(i) for i in x ]))
        else:
            for i in options[0]: 
                keys.append(str(self.id) + '_' + i)


        if not keys:
            keys = [ "%s_" % self.id]

        # print keys
        Variant.objects.filter(product_id=self.id).update(deleted=True)

        for key in keys:
            variant , is_created = Variant.objects.get_or_create(product_id=self.id, key=key, sku=self.sku)
           #if item.cost == 0:
           #    item.cost = self.cost
            if variant.weight == 0:
                variant.weight = self.weight
            
            variant.deleted = False
            variant.save()

    def __unicode__(self):
        # return self.sku + '|' + self.name
        return self.sku

    def get_images(self):
        #images = self.productimage_set.order_by('order').all()
        images = self.productimage_set.order_by('-id').all()
        return images

    # def get_image_thumb(self):
    #     images = self.productimage_set.order_by('id').filter(deleted=False).first()

    #     if images:
    #         image_url = str(images.image)
    #         image_url_array = image_url.split('/')
    #         if image_url_array:
    #             url = "http://d1cr7zfsu1b8qs.cloudfront.net/pimg/420/355206.jpg"
    #         else:
    #             url = "/static/admin/img/100x100.png"
    #         # url = 'file:///'+str(images.image)
    #         # if image_url_array[2]:
    #         #     url = '/static/'+image_url_array[0]+'/'+image_url_array[1]+'/'+image_url_array[2]
    #         # else:
    #         #     url = "/static/admin/img/100x100.png"  
    #     else:
    #         url = "/static/admin/img/100x100.png"
    #     # return format_html(u'<img src="%s" />' % (url))
    #     return url

    # def get_celebrityimages_thumb(self):
    #     images = self.celebrityimages_set.order_by('id').filter(deleted=False).first()
    #     if images:
    #         image_url = str(images.image)
    #         image_url_array = image_url.split('/')
    #         if image_url_array:
    #             url = "http://d1cr7zfsu1b8qs.cloudfront.net/pimg/420/355206.jpg"
    #         else:
    #             url = "/static/admin/img/100x100.png"
    #     else:
    #         url = "/static/admin/img/100x100.png"
        # return format_html(u'<img src="%s" />' % (url))
        # return url

    def update_sku(self):
        tmp=self.category.code+self.id5
        Product.objects.filter(id=self.id).update(sku=tmp)
    def stock_source(self):
        if self.source == '采购':
            if self.stock == -1:
                self.stock = -99
                self.save()
        if self.source == '做货' or self.source == '库存限制销售':
            if self.stock == -99:
                self.stock = -1
                self.save()
    def save(self, *args, **kwargs):
        res = self.es_index()
        super(Product, self).save(*args, **kwargs)

    #产品库存状态限制数据保存
    def product_stock_limit(self,request):
        limit = str(request.POST.get('no_limit_stock'))

        if limit == '1':
            query = Product.objects.filter(id=self.id).update(stock=-99)
            product = Product.objects.filter(id=self.id).first()

        if limit == '0':
            query = Product.objects.filter(id=self.id).update(stock=-1)
            product = Product.objects.filter(id=self.id).first()

            ONE_SIZE = request.POST.get('stock_ONE SIZE',0)
            S = request.POST.get('stock_S',0)
            M = request.POST.get('stock_M',0)
            L = request.POST.get('stock_L',0)
            XL = request.POST.get('stock_XL',0)
            XXL = request.POST.get('stock_XXL',0)
            XXXL = request.POST.get('stock_XXXL',0)
            XXXXL = request.POST.get('stock_XXXXL',0)
            size_list = [['S',S],['M',M],['L',L],['XL',XL],['XXL',XXL],['XXXL',XXXL],['XXXL',XXXL],['XXXXL',XXXXL],['one size',ONE_SIZE]]

            for size in size_list:
                if size[1]:
                    query = Stocks.objects.filter(product_id=self.id,attributes=size[0])
                    if query:
                        query1 = Stocks.objects.filter(product_id=self.id,attributes=size[0]).update(stocks=size[1])
                    else:
                        query2 = Stocks.objects.create(product_id=self.id,attributes=size[0],stocks=size[1])

    def category_product_save(self,request):
        category_id=request.POST.getlist('category')
        category=[]
        product_id=self.id
        query=[]
        query_get=CategoryProduct.objects.filter(product_id=product_id).values_list('category_id')
        #数据类型转换
        for query_id in query_get:
            for query_gid in query_id:
                query.append(int(query_gid))
        for query_id in category_id:
            category.append(int(query_id))
        #筛选数据
        category_all=  list(set(category).intersection(set(query)))
        category_id=list(set(category).difference(set(category_all))) 
        query_id=list(set(query).difference(set(category_all))) 
        #数据库操作
        #create
        for category in category_id:
            query_create=CategoryProduct.objects.get_or_create(category_id=category,product_id=product_id,deleted=False)
        #deleled=true
        for query in query_id:
            deleted_id=CategoryProduct.objects.filter(product_id=product_id,category_id=query).first()  
            query_set=CategoryProduct.objects.filter(id=deleted_id.id).update(deleted=True)
        #deleted=false
        for category in category_all:
            deleted_id=CategoryProduct.objects.filter(product_id=product_id,category_id=category).first()
            if deleted_id.deleted:
               query_set=CategoryProduct.objects.filter(id=deleted_id.id).update(deleted=False)             
       
				
    """产品列表的查询"""
    def product_list(self,search):
        if not search:
            return Product.objects.filter(deleted=0).order_by('id')
        else:
            return Product.objects.filter(deleted=0,sku__contains=search).order_by('id')

    def priceto(self):
        expired_time = nowtime()
        spro = carts.models.Spromotions.objects.filter(product_id=self.id,expired__gte=expired_time).order_by('-id').first()
        if spro:
            return spro.price
        else:
            return self.price

    def attr(self):
        attrs = Productitem.objects.filter(product_id=self.id).values("attribute").all()
        # print type(ProductAttribute.objects.filter(product_id=self.id))  # queryset
        # values  [{'name': 'li'}, {}]
        # values_list [('li', ), ('zhang', ), ()]
        # values_list('name', flat=True) ['li', 'zhang']

        # info = values_list('order__user__username', 'age')

        # for first_name, age in info:
        #     [order__user__username]

        #if attrs:
        attr = {}
        if attrs:
            default_catalog = u''
            cp = CategoryProduct.objects.filter(product_id=self.id,category__visibility=1).values('category_id')
            if cp:
                for cid in cp:
                    default_catalog += str(cid['category_id']) + ' '

            color_value = ''
            pro_filters = ProductFilter.objects.filter(product_id=self.id)
            if pro_filters:
                for i in pro_filters:
                    filters = Filter.objects.filter(id=i.filter_id).first()
                    if filters:
                        if filters.name == 'color':
                            color_value = filters.options

            if not color_value:
                new_s = self.filter_attributes.split(';')
                if new_s:
                    color_value = new_s[0]

            size_value = u''
            attributes = u''

            for i in attrs:
                size_value += i['attribute'].upper()+' '
                attributes += 'size'+i['attribute'].upper()+' '

            size_value = size_value[:-1]
            attributes = attributes[:-1]
            attr['size_value'] = size_value
            attr['attributes'] = attributes
            attr['color_value'] = color_value
            attr['default_catalog'] = default_catalog
        else:
            attr['size_value'] = u''
            attr['attributes'] = u''
            attr['color_value'] = u''
            attr['default_catalog'] = u''
        return attr

    def cover_image(self):
        if self.configs:
            cimg = phpserialize.loads(self.configs)
            cover_image = {}
           # cimg = "{'default_image': 1, 'images_order': '1,2,3'}"
            if 'default_image' in cimg.keys():
                cover_image['id'] = cimg['default_image']
                cover_image['suffix'] = 'jpg'
                cover_image['status'] = 1
            elif 'images_order' in cimg.keys():
                img_order = cimg['images_order'].split(',')
                if img_order[0]:
                    cover_image['id'] = img_order[0]
                    cover_image['suffix'] = 'jpg'
                    cover_image['status'] = 1 
                #print cover_image
            cover_image = phpserialize.dumps(cover_image)
            return cover_image
        else:
            return ''
        
    """产品图片序列化保存"""
    def imagesave(self,request): 
        # is_default = request.POST.get('is_default','')
        productimages = ProductImage.objects.filter(product_id=self.id).order_by('-id')
        images_id = []
        config_set = {}
        is_default_count = 0
        for productimage in productimages:
            imageid = str(productimage.id)
            images_id.append(imageid)
            if int(productimage.is_default) == 1:
                is_default_count += 1
        
        #判断是否勾选了多个默认
        # if is_default_count > 1:
        #     messages.error(request,u'默认图片的数量不能大于1')

        image_default = ProductImage.objects.filter(product_id=self.id,is_default=1).order_by('-id').first()
        images_order = []
        #如果有默认图片，把默认图片id放在序列化的第一位
        if images_id:
            if image_default:
                for i in images_id:
                    if int(i) == int(image_default.id):
                        images_order.append(i)
                for i in images_id:
                    if int(i) != int(image_default.id):
                        images_order.append(i)

                config_set['default_image'] = int(image_default.id)
            #没有默认图片随意选取一张作为默认图片
            else:
                config_set['default_image'] = int(images_id[0])
                images_order = images_id

        images_order = ','.join(images_order)

        config_set['images_order'] = images_order

        configs = phpserialize.dumps(config_set)

        self.configs=configs
        self.save()


    """产品图片序列化保存(包含默认图片和图片排序)"""
    def imagesave_new(self,request): 
        url = request.path
        #获取所有的产品图片
        productimages = ProductImage.objects.filter(product_id=self.id).order_by('position')
        images_id = []
        images_id1 = []
        config_set = {}
        for productimage in productimages:
            #如果图片的排序是0，则把图片放在最后，其他的按1234排序
            if productimage.position == 0:
                images_id1.append(str(productimage.id))
            else:
                images_id.append(str(productimage.id))

        images_id.extend(images_id1)

        image_default = ProductImage.objects.filter(product_id=self.id,is_default=1).order_by('position').first()
        images_order = []

        # 如果有默认图片，把默认图片id放在序列化的第一位,其他图片按排序放置
        if images_id:
            if image_default:
                for i in images_id:
                    if int(i) == int(image_default.id):
                        images_order.append(i)
                for i in images_id:
                    if int(i) != int(image_default.id):
                        images_order.append(i)

                config_set['default_image'] = int(image_default.id)
            #没有默认图片随意选取一张作为默认图片，及位置排序最小的一张图片
            else:
                config_set['default_image'] = int(images_id[0])
                images_order = images_id

        images_order = ','.join(images_order)

        config_set['images_order'] = images_order

        configs = phpserialize.dumps(config_set)

        self.configs=configs
        self.save()



    """红人秀图片保存时去掉simg/,只保留图片名称"""
    def change_celebrity_imagename(self,request):
        celebrity_images = CelebrityImages.objects.filter(product_id=self.id)
        for celebrity_image in celebrity_images:
            image_name = celebrity_image.image
            if image_name:
                image_name = str(image_name)
                if image_name.find('simages/') != -1:
                    index = image_name.find('simages/')+8
                    name = image_name[index:]
                    query = CelebrityImages.objects.filter(id=celebrity_image.id).update(image=name)
    # 不在后台生成产品数据缓存
    def memcache_product(self,request):
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        #查询数据
        cursor = connection.cursor()
        query = 'select * from products_product where id = '+str(self.id)
        cursor.execute(query)
        #数据字段整合
        col_names = [desc[0] for desc in cursor.description]
        res = cursor.fetchone()
        data = dict(zip(col_names, res))
        # product attribute
        items = Productitem.objects.filter(product_id=self.id).values('status','attribute','stock','product_id')
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
                stock = item['stock']

                # instock
                if item['stock']>0:
                    instock = instock + 1

                # status
                if item['status'] == 1:
                    status = status+1

            attributes = {'Size': attribute}
            data['attributes'] = attributes
            data['instock'] = instock
            data['stock'] = stock
            data['status'] = status
        #product filter
        filters = ProductFilter.objects.filter(product_id=self.id).all()
        if filters:
            filter_str = ''
            for filter in filters:
                    filter_str = filter_str +str(filter) + ';'
                # print filter_str
            data['filter_attributes'] = filter_str.strip(';')
        #序列化
        product =  phpserialize.dumps(data)
        #print '----',product
        #设置缓存
        name = 'productcache1/'+str(self.id)
        cache.set(name,product,3600)
    # 调用产品接口，删除产品数据缓存，有前台生成产品页数据缓存
    def memcache_product1(self):
        url = settings.BASE_URL+'api/delete_product_cache'
        # url = 'http://local.oldchoies.com/api/delete_product_cache'
        postData = self.id
        data = json.dumps(postData)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req,urllib.urlencode({'id':data}))

    def default_productimage_memcache(self,request):
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)

        image_default = ProductImage.objects.filter(product_id=self.id,is_default=1).order_by('-id').first()
        if image_default:
            image_id = image_default.id
            cache_key = 'site_image_' + str(image_id)

            cache_data = {}
            cache_data['id'] = str(image_default.id)
            cache_data['product_id'] = str(image_default.product_id)
            cache_data['type'] = str(image_default.type)
            cache_data['suffix'] = str(image_default.suffix)
            cache_data['status'] = str(image_default.status)

            cache_data = phpserialize.dumps(cache_data)
            cache.set(cache_key,cache_data,3600)

    def productimage_memcache(self,request):
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)

        cache_key = 'prodct_images_' + str(self.id)
        productimages =  ProductImage.objects.filter(product_id=self.id,type=1)
        i = 0
        cache_data = {}
        for productimage in productimages:
            data = {}
            data['id'] = productimage.id
            data['suffix'] = productimage.suffix
            data['status'] = productimage.status
            cache_data[i] = data
            i += 1
        cache_data = phpserialize.dumps(cache_data)
        cache.set(cache_key,cache_data,3600)
    # 根据item状态更新产品status字段
    def product_status(self):
        items = Productitem.objects.filter(product_id=self.id).all()
        status = 0
        for item in items:
            if item.status:
                status = 1
        if status:
            self.status = 1
        else:
            self.status = 0
        self.save()

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product)
    #attribute = models.ForeignKey(Attribute)
    name = models.CharField(max_length=100)
    options = models.TextField(blank=True, default="", help_text=u"不同尺码以','隔开")


    def get_options(self):
        return self.options.split(',')

    def __unicode__(self):
        return self.name

class ProductFilter(models.Model):
    product = models.ForeignKey(Product)
    filter = models.ForeignKey(Filter)
    options = models.TextField(blank=True, default="", help_text="split by ,")

    def __unicode__(self):
        return self.options

   #class Meta:
   #    verbose_name = u'产品属性'
   #    verbose_name_plural = u'产品属性'


class ProductImage(models.Model):
    image = models.ImageField(upload_to=get_product_image_upload_path, blank=True,null=True,verbose_name=u"图片地址")
    product = models.ForeignKey(Product, verbose_name=u"产品名称")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    suffix = models.CharField(max_length=100,default='jpg', verbose_name=u"图片后缀名")
   #img_updater = models.ForeignKey(User, related_name='img_updater', verbose_name=u"修改图片人员")
   #img_adder = models.ForeignKey(User, related_name='img_adder', verbose_name=u"新增图片人员")
    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")
    is_default = models.BooleanField(default=0,blank=True, verbose_name=u'设置为默认')
    status = models.IntegerField(default=1, verbose_name=u"状态")
    position = models.IntegerField(default=0, verbose_name=u"图片排序",help_text=u"数字越小排序越靠前")
    type = models.IntegerField(default=1, verbose_name=u"类型")

    class Meta:
        verbose_name = u'产品图片'
        verbose_name_plural = u'产品图片'
 
    def __unicode__(self):
        return 'Image %s' % self.id

class Variant(models.Model):

    STATUS = (
            (1, u'可销售'),
            (0, u'停止销售'),
        )

    product = models.ForeignKey(Product)
    key = models.CharField(max_length=200)

    sku = models.CharField(max_length=200, db_index=True)
    weight = models.FloatField(default=0.0, help_text=u"KG")
    qty = models.IntegerField(default=0)
    price = models.FloatField(default=0)
    status = models.IntegerField(choices=STATUS, default=1)
    image = models.ImageField(upload_to=get_product_image_upload_path)

    created = UnixDateTimeField(auto_now_add=True)
    updated = UnixDateTimeField(auto_now=True )
    deleted = models.BooleanField(default=False)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
        #return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    def _update(self):
        #self.sku = self.product.sku + self.key
        self.status = True
        #self.price = self.product.price
        self.save()

    class Meta:
        unique_together = ('key', 'product',)
       #verbose_name = u'属性产品'
       #verbose_name_plural = u'属性产品'

    def __unicode__(self):
        return self.key

class CategoryProduct(models.Model):
    category = models.ForeignKey(Category,verbose_name=u"分类名称")
    product = models.ForeignKey(Product, verbose_name=u"产品名称")
    position = models.IntegerField(default=0,verbose_name=u"排序")
    positiontwo = models.IntegerField(default=0)
    deleted = models.BooleanField(default=False,blank=True, verbose_name=u"是否已删除")
    # def __unicode__(self):
    #     return self.category
    class Meta:
        verbose_name = '产品分类'
        verbose_name_plural = '产品分类'
class Brands(models.Model):
    #attribute = models.ForeignKey(Attribute)
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    brief = models.CharField(max_length=100, verbose_name=u"描述")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'品牌'
        verbose_name_plural = u'品牌'

class CelebrityImages(models.Model):
    TYPE= (
            (1,u'红人'),
            (2,u'关联'),
            (3,u'红人关联'),
        )

    product = models.ForeignKey(Product)
    image = models.ImageField(upload_to=get_celebrity_image_upload_path, verbose_name=u"图片地址")
    position = models.IntegerField(default=0, verbose_name=u"排序")
    # site_id = models.BooleanField(default=1)
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')
    type = models.IntegerField(choices=TYPE, default=1,verbose_name=u"关联类型")
    link_sku=models.CharField(max_length=150,default='',blank=True, null=True,verbose_name="关联SKU", help_text=u"产品SKU逗号分隔,type=1时为红人id")
    is_show = models.BooleanField(default=1, verbose_name=u"展示")

    #新增红人id字段
    celebrity = models.ForeignKey(Celebrits,blank=True, null=True, verbose_name='celebrity_id')
    deleted = models.BooleanField(default=False,blank=True, verbose_name=u"是否已删除")
    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")

    def __unicode__(self):
        return self.link_sku

class Tags(models.Model):

    name = models.CharField(max_length=300, verbose_name=u"标签名称")
    link = models.CharField(max_length=100, verbose_name=u"标签url")
    position = models.IntegerField(default=0, verbose_name=u"排序")

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True)
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True)
    deleted = models.BooleanField(default=False,blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'标签'
        verbose_name_plural = u'标签'

class Set(models.Model):
    name = models.CharField(max_length=100)
    brief = models.CharField(max_length=100, verbose_name=u"描述")
    # site_id = models.BooleanField(default=1)

    label = models.CharField(max_length=100)
    catemanger = models.CharField(max_length=100, verbose_name=u"品类经理")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'品类'
        verbose_name_plural = u'品类'

class TagProduct(models.Model):
    TYPE= (
            (1,u'红人'),
            (2,u'关联'),
            (3,u'红人关联'),
        )

    tag = models.ForeignKey(Tags)
    product = models.ForeignKey(Product)
    position = models.IntegerField(default=0, verbose_name=u"排序")

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True)
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True)
    deleted = models.BooleanField(default=0,blank=True)

    def __unicode__(self):
        return str(self.id)

class Stocks(models.Model):
    product = models.ForeignKey(Product)
    attributes = models.CharField(max_length=100,default='',blank=True,null=True)
    stocks = models.IntegerField(default='',blank=True)
    isdisplay = models.IntegerField(default=1)
    test = models.CharField(max_length=100,default='',blank=True,null=True)

    def __unicode__(self):
        return str(self.id)

class Marks(models.Model):
    category = models.ForeignKey(Category)
    product = models.ForeignKey(Product)
    mark = models.ForeignKey('self',blank=True,null=True)
    mark_name = models.CharField(max_length=122,default='',blank=True,null=True)
    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True)
    sku = models.CharField(max_length=20,default='',blank=True,null=True)

    def __unicode__(self):
        return str(self.id)

class Daily(models.Model):
    day = models.IntegerField(null=True)
    product = models.ForeignKey(Product)
    clicks = models.IntegerField(null=True)
    quick_clicks = models.IntegerField(null=True)
    add_times = models.IntegerField(null=True)
    hits = models.IntegerField(null=True)

class Relatedproduct(models.Model):
    product = models.ForeignKey(Product)
    related_product_id = models.IntegerField(null=True)

class Productitem(models.Model):
    STOCK = (
        (0,u'下架'),
        (1,u'上架'),
    )
    product = models.ForeignKey(Product,blank=True,null=True)
    status = models.IntegerField(choices=STOCK,default=1,verbose_name=u'状态')
    sku = models.CharField(max_length=255,blank=True,null=True)
    attribute = models.CharField(max_length=255,blank=True,null=True,verbose_name=u'尺码')
    stock = models.IntegerField(default=-99,verbose_name=u'库存量')

    def __unicode__(self):
        return str(self.sku)

class Trans_es(models.Model):
    product = models.ForeignKey(Product,blank=True,null=True)
    name = models.CharField(default='',max_length=255,blank=True,null=True,)
    brief = models.TextField(default='',blank=True,null=True,)
    description = models.TextField(default='',blank=True,null=True,)

    def __unicode__(self):
        return str(self.product)

class Trans_de(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True)
    name = models.CharField(default='',max_length=255,blank=True,null=True,)
    brief = models.TextField(default='',blank=True,null=True,)
    description = models.TextField(default='', blank=True, null=True, )
    def __unicode__(self):
        return str(self.product)

class Trans_fr(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True)
    name = models.CharField(default='',max_length=255,blank=True,null=True,)
    brief = models.TextField(default='',blank=True,null=True,)
    description = models.TextField(default='', blank=True, null=True, )
    def __unicode__(self):
        return str(self.product)

class TransCategory(models.Model):
    name = models.CharField(max_length=255)
    meta_title = models.CharField(blank=True, max_length=100, default='', verbose_name=u"SEO标题")
    meta_keywords = models.TextField(blank=True,null=True,default='', verbose_name=u"SEO关键字")
    meta_description = models.TextField(blank=True,null=True, verbose_name=u"SEO描述")
    category_id = models.IntegerField(null=True)
    lang = models.CharField(max_length=255,null=True)

class ColorProduct(models.Model):
    product = models.ForeignKey(Product)
    group = models.IntegerField()

    class Meta:
        verbose_name = u'同款不同色'
        verbose_name_plural = u'同款不同色'