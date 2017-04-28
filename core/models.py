# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django_unixdatetimefield import UnixDateTimeField
from django.db import models
from mptt.models import MPTTModel
import datetime
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
import products
import urllib
import urllib2
import json
class Country(models.Model):
    IS_ACTIVE = (
            (1, u'是'),
            (0, u'否'),
        )

    name = models.CharField(max_length=100)
    cn_name = models.CharField(max_length=100, default="", blank=True,null=True)
    isocode = models.CharField(max_length=2, default='', blank=True,null=True)
    number = models.IntegerField(default=0)
    position = models.IntegerField(default=0, verbose_name=u"排序")
    is_active = models.IntegerField(choices=IS_ACTIVE, default=1, verbose_name=u"是否展示")
    brief = models.CharField(blank=True,max_length=100, verbose_name=u"描述")

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True)
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True)
    deleted = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = u'国家'
        verbose_name_plural = u'国家'

    def __unicode__(self):
        return "%s|%s|%s" % (self.isocode, self.name, self.cn_name)

class Notify(models.Model):
    title = models.CharField(max_length=250)
    action = models.CharField(max_length=250, blank=True)
    content = models.TextField(default="", blank=True)
    user = models.ForeignKey(User, null=True)
    is_read = models.BooleanField(default=False)
    read_time = UnixDateTimeField()

    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'信息'
        verbose_name_plural = u'信息'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
        #return urlresolvers.reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))


class Sites(models.Model):
    # Site Basic Information
    domain = models.CharField(max_length=255, verbose_name=u"Domain")
    email = models.EmailField(blank=True, verbose_name=u"Email")
    # line = models.ForeignKey(Line,null=True,verbose_name=u"Line")
    line_id = models.IntegerField(default=0,blank=True, null=True,verbose_name=u"Line")
    ssl = models.BooleanField(default=1, blank=True, verbose_name=u"SSL")
    is_active = models.BooleanField(default=1, blank=True)
    fb_login = models.BooleanField(default=1, blank=True)
    is_pay_insite = models.BooleanField(default=1, blank=True)
    erp_enabled = models.BooleanField(default=0, blank=True)
    promotion_coupon = models.BooleanField(default=0, blank=True)
    per_page = models.IntegerField(default=24, verbose_name=u"Items per page")
    forum_moderators = models.CharField(max_length=255, blank=True, verbose_name=u"Forum moderators")

    # Site Basic SEO
    meta_title = models.TextField(default="", blank=True, verbose_name=u"Global Title")
    meta_keywords = models.TextField(default="", blank=True, verbose_name=u"Global Keywords")
    meta_description = models.TextField(default="", blank=True, verbose_name=u"Global Meta Description")
    robots = models.TextField(default="", blank=True, verbose_name=u"Robots.txt")
    stat_code = models.TextField(default="", blank=True, verbose_name=u"Stat Code")
    currency = models.CharField(max_length=255,default='', verbose_name=u"币种") 
    product = models.CharField(max_length=32,default='product', verbose_name=u"产品路由")  
    catalog = models.CharField(max_length=32, default='', blank=True, null=True )  
    promotion = models.CharField(max_length=32,default='promotion', blank=True, null=True)  
    suffix = models.CharField(max_length=32,default='', blank=True, null=True)  
    cc_secure_code = models.CharField(max_length=10,default='', blank=True, null=True)  
    cc_payment_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_payment_id = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_tiny_payment_id = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_payment_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_submit_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_notify_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_return_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_cancel_return_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_logo_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_api_version = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_api_version = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_api_user = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_api_pwd = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_api_signa = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_ec_notify_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_ec_return_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    pp_sync_url = models.CharField(max_length=255,default='', blank=True, null=True)  
    ticket_center = models.CharField(max_length=255,default='', blank=True, null=True)  
    fb_api_id = models.CharField(max_length=255,default='', blank=True, null=True)  
    fb_api_secret = models.CharField(max_length=255,default='', blank=True, null=True)  
    lang = models.CharField(max_length=8,default='', blank=True, null=True)  
    fb_api_secret = models.CharField(max_length=255,default='', blank=True, null=True)  
    elastic_host = models.CharField(max_length=255,default='', blank=True, null=True)  
 
    cc_payment_id = models.IntegerField(default=0, blank=True,null=True)

    route_type = models.IntegerField(default=2,blank=True, null=True,)
    # continue = models.IntegerField(default=0,blank=True, null=True,)
    checkout = models.IntegerField(default=0,blank=True, null=True,)
    ppec = models.IntegerField(default=0,blank=True, null=True,)
    ppjump = models.IntegerField(default=0,blank=True, null=True,)
    globebill = models.IntegerField(default=0,blank=True, null=True,)


    class Meta:
        verbose_name = u'站点配置'
        verbose_name_plural = u'站点配置'
        

class Currencies(models.Model):
    name = models.CharField(max_length=50, verbose_name=u"名称")
    fname = models.CharField(max_length=50, verbose_name=u"完整名称")
    code = models.CharField(max_length=50, verbose_name=u"符号")
    rate = models.DecimalField(max_digits=12, decimal_places=4, verbose_name=u"汇率")

    class Meta:
        verbose_name = u'站点支持货币列表'
        verbose_name_plural = u'站点支持货币列表'
    def delete_currencies_cache(self):
        url = settings.BASE_URL + 'api/delete_currencies_cache'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
class Mail_types(models.Model):
    name = models.CharField(max_length=255)

    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'邮件分类'
        verbose_name_plural = u'邮件分类'


class Mails(models.Model):
    type_id = models.IntegerField(default=0,blank=True, null=True, verbose_name=u"邮件类型")
    title = models.CharField(max_length=255,blank=True, null=True,default='', verbose_name=u"邮件标题")
    lang = models.CharField(max_length=10,blank=True, null=True,default='',)
    type = models.CharField(max_length=255,blank=True, null=True,default='',)
    template = models.TextField(default="", blank=True, verbose_name=u"邮件内容")
    is_active = models.BooleanField(default=1, verbose_name=u"is_active")

    created = UnixDateTimeField(auto_now_add=True,blank=True, null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True, null=True, verbose_name=u"修改时间")

    class Meta:
        verbose_name = u'邮件模板列表'
        verbose_name_plural = u'邮件模板列表'


class Mail_logs(models.Model):
    TYPE = (
        (1, u'unpaid'),
        (2, u'birth'),
        (3, u'vip'),
        (4, u'coupon'),
        (5, u'whishlist'),
    )

    Tables = (
        (1, u'order'),
        (2, u'customer'),
        (3, u'order_payments'),
        (4, u'coupon'),
    )

    type = models.IntegerField(choices=TYPE, default=1, verbose_name=u"Type")
    table = models.IntegerField(choices=Tables, default=1,blank=True,null=True, verbose_name=u"Table")
    table_id = models.IntegerField(default=0, verbose_name=u"Table_id")
    email = models.CharField(default="", max_length=255, verbose_name=u"Email")
    status = models.CharField(default="", max_length=255, verbose_name=u"Status")
    send_date = UnixDateTimeField(auto_now_add=True, max_length=255, verbose_name=u"Send Date")

    class Meta:
        verbose_name = u'邮件日志列表'
        verbose_name_plural = u'邮件日志列表'


class Docs(models.Model):
    name = models.CharField(max_length=255)
    link = models.CharField(default="", max_length=255)
    order = models.IntegerField(default=0,blank=True,null=True)
    is_active = models.BooleanField(default=1, verbose_name=u"is_active")
    content = models.TextField(blank=True,null=True, default="")
    meta_title = models.TextField(blank=True, default="")
    meta_keywords = models.TextField(blank=True, default="")
    meta_description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = u'站点文案en'
        verbose_name_plural = u'站点文案en'


class Docs_es(models.Model):
    name = models.CharField(max_length=255)
    link = models.CharField(default="", max_length=255)
    order = models.IntegerField(default=0,blank=True,null=True)
    is_active = models.BooleanField(default=1, verbose_name=u"is_active")
    content = models.TextField(blank=True,null=True, default="")
    meta_title = models.TextField(blank=True, default="")
    meta_keywords = models.TextField(blank=True, default="")
    meta_description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = u'站点文案es'
        verbose_name_plural = u'站点文案es'

class Vip_types(models.Model):
    level = models.IntegerField(default=0, verbose_name=u"客户等级")
    condition = models.CharField(default="0", max_length=20,verbose_name=u"金额条件(<=金额)")
    limit = models.CharField(default="1000", max_length=20,verbose_name=u"积分使用限度单位")
    unit = models.CharField(default="50", max_length=20,verbose_name=u"积分使用金额单位")
    discount = models.FloatField(default="1.00", max_length=20,verbose_name=u"享受产品折扣率")
    returns = models.IntegerField(default="1",verbose_name=u"订单积分返还倍数")
    brief = models.CharField(default="", max_length=30,verbose_name=u"描述")

    class Meta:
        verbose_name = u'vip客户等级'
        verbose_name_plural = u'vip客户等级'

class Site_clicks(models.Model):
    day = models.IntegerField(default=0,)
    add_to_cart = models.IntegerField(default=0,)
    cart_view = models.IntegerField(default=0,)
    continues = models.IntegerField(default=0,)
    checkout = models.IntegerField(default=0,)
    ppec = models.IntegerField(default=0,)
    cart_login = models.IntegerField(default=0,)
    cart_checkout = models.IntegerField(default=0,)
    proceed = models.IntegerField(default=0,)
    globebill = models.IntegerField(default=0,)
    ppjump = models.IntegerField(default=0,)
    card_pay = models.IntegerField(default=0,)
    log = models.TextField(default='',)
    cart_to_cookie = models.IntegerField(default=0,)
    cookie_to_cart = models.IntegerField(default=0,)
    card_return = models.IntegerField(default=0,)


class Carriers(models.Model):
    isocode = models.CharField(max_length=32,blank=True,default='',null=True)
    carrier = models.CharField(max_length=20,blank=True,default='',null=True)
    carrier_name = models.CharField(max_length=255,blank=True,default='',null=True)
    interval = models.TextField(blank=True,null=True,default='')
    formula = models.CharField(max_length=100,blank=True,default='',null=True)
    brief = models.TextField(blank=True,null=True,default='')
    position = models.IntegerField(default=0,blank=True,)

class Searchwords(models.Model):
    words = models.CharField(max_length=50,blank=True,default='',null=True,verbose_name=u"搜索词")
    amount = models.IntegerField(default=0,null=True,blank=True)


class Trans(models.Model):
    product = models.ForeignKey('products.Product',verbose_name=u'产品')
    trans_de = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'Trans_de')
    trans_es = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'Trans_es')
    trans_fr = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'Trans_fr')
    
    class Meta:
        verbose_name = u'产品小语种翻译'
        verbose_name_plural = u'产品小语种翻译'
            

class Pla(models.Model):
    label=(
        (1,u'颜色'),
        (2,u'分类'),
        (3,u'价格范围'),
        (4,u'爆款'),
        (5,u'自定义'),
    )
    type=(
        (1,u'自动获取类feed'),
        (0,u'自定义类feed')
    )
    title = models.CharField(max_length=255,default='',verbose_name=u'定义开头、结尾,++++分割')
    description = models.CharField(max_length=255,default='',verbose_name=u'定义开头、结尾，++++分割')
    custom_label_0 = models.IntegerField(choices=label,default=1)
    custom_label_1 = models.IntegerField(choices=label,default=2)
    custom_label_2 = models.IntegerField(choices=label,default=3)
    custom_label_3 = models.IntegerField(choices=label,default=4)
    custom_label_4 = models.IntegerField(choices=type,default=5)
    custom_label = models.CharField(max_length=255, default='',verbose_name=u'custome_label_ 自定义内容' )
    promotion = models.CharField(max_length=255,default='',verbose_name=u'自定义输入')
    country = models.CharField(max_length=255,default='',verbose_name=u'国家')
    feed = models.CharField(max_length=255,default='',verbose_name=u'文件名')
    status = models.IntegerField(default=0,verbose_name=u'状态，供脚本使用，1时脚本使用该条数据')
    uid = models.CharField(max_length=255,default='',verbose_name=u'SKU-Size-US-自定义')
    position = models.CharField(max_length=255,default='',verbose_name=u'title descprition位置信息')
    lang = models.CharField(max_length=255,default='',verbose_name=u'')
    type = models.IntegerField(choices=type,default=0,verbose_name=u'1,自动获取的feed;0,后台自定义的feed')