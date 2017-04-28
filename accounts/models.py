# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django_unixdatetimefield import UnixDateTimeField
from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AbstractUser, User
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import *
from orders.models import Order
from products.models import Product

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
#AbstractUser._meta.get_field('email')._unique = True
#AbstractUser.USERNAME_FIELD = 'email'
#AbstractUser.REQUIRED_FIELDS = ['username']

User._meta.get_field('email')._unique = True

User.USERNAME_FIELD = 'email'
User.REQUIRED_FIELDS = ['username', ]


class Customers(models.Model):
    STATUS = (
            (1, u'正常'),
            (0, u'屏蔽'),
        )

    GENDER = (
            (0, u'Male'),
            (1, u'Female'),
            (2, u'Other'),
        )

    FACEBOOK = (
            (1, u'是'),
            (0, u'否'),
        )

    PPEC = (
            (-1, u'非PPEC用户'),
            (0, u'PPEC用户没登录'),
            (1, u'登录用户'),
        )

    FLAG = (
            (0, u'正常客户'),
            (1, u'非正常客户'),
            (3, u'批发客户'),
        )

    VIP = (
            (1, u'是'),
            (0, u'否'),
        )

    # site_id = models.BooleanField(default=True, verbose_name="Site id")
    email = models.EmailField(default='',unique=True, verbose_name=u"客户邮箱")
    password = models.CharField(max_length=50, default='',blank=True,null=True)
    firstname = models.CharField(max_length=100, default='',blank=True,null=True)
    lastname = models.CharField(max_length=100, default='',blank=True,null=True)
    birthday = UnixDateTimeField(blank=True, null=True, verbose_name="生日")
    #birth = models.CharField(max_length=100,default='', verbose_name=u"出生日期")
    status = models.IntegerField(choices=STATUS, default=1,blank=True,null=True,db_index=True, verbose_name=u"状态")
    gender = models.IntegerField(choices=GENDER, default=1,blank=True,null=True, verbose_name=u"性别")
    # country = models.ForeignKey('core.Country',default='', null=True, blank=True,max_length=20,verbose_name="国家")
    country = models.CharField(max_length=100, default='',blank=True,null=True)
    points = models.IntegerField(default=0, blank=True,null=True,verbose_name=u"积分")
    order_total = models.CharField(default=0,max_length=50,blank=True,null=True, verbose_name=u"订单总金额")
    is_facebook = models.IntegerField(choices=FACEBOOK, default=0,null=True, verbose_name=u"fb用户")
    ip = models.CharField(max_length=20,blank=True,null=True,verbose_name="IP",)
    vip_level = models.IntegerField(default=0, blank=True,null=True, verbose_name=u"VIP等级")
    last_login_time = UnixDateTimeField(blank=True, null=True,db_index=True, verbose_name=u"最后一次登录时间")
    last_login_ip = models.CharField(max_length=20,blank=True,null=True,verbose_name="最后一次登录IP",)
    lang = models.CharField(max_length=10, default='',blank=True,null=True)
    ppec_status = models.IntegerField(choices=PPEC,blank=True,null=True, default=0, verbose_name=u"PPEC用户状态") 
    #ip_country = models.CharField(max_length=20,verbose_name="IP所属国家")
    flag = models.IntegerField(choices=FLAG, default=0,blank=True,null=True, verbose_name=u"顾客标识") 
    is_vip = models.IntegerField(choices=VIP, default=1,blank=True,null=True, verbose_name=u"VIP状态")
    vip_start = UnixDateTimeField(blank=True, null=True, verbose_name="会员开始时间")
    vip_end = UnixDateTimeField(blank=True, null=True, verbose_name="初始会员到期时间")
    users_admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True,db_index=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否已删除")

    give_points = models.BooleanField(default=False, blank=True)
    ip_country = models.CharField(max_length=30,default='',blank=True,null=True)
    #orders = models.ForeignKey('orders.Order',null=False,default=0)
    #待添加
    class Meta:
        verbose_name = u'用户管理'
        verbose_name_plural = u'用户管理'
        # unique_together = ('status', 'created')

    def __unicode__(self):
        return self.email

class Address(models.Model):
    IS_DEFAULT = (
            (1,u'默认地址'),
            (0,u'普通地址'),
        )

    user = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True, null=True)
    customer = models.ForeignKey(Customers,null=True)
    firstname = models.CharField(max_length=255, default='', blank=True, null=True)
    lastname = models.CharField(max_length=255, default='', blank=True, null=True)
    address = models.CharField(max_length=500, default='', blank=True, null=True)
    address1 = models.CharField(max_length=500, default='', blank=True, null=True)
    city = models.CharField(max_length=250, default='', blank=True, null=True)
    state = models.CharField(max_length=250, default='', blank=True, null=True)

    # country = models.ForeignKey('core.Country', null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=100, default='', blank=True, null=True)
    phone = models.CharField(max_length=100, default='', blank=True, null=True)

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否已删除")

    #add field
    # site_id = models.BooleanField(default=1)
    is_default = models.BooleanField(choices=IS_DEFAULT, default=0)

    class Meta:
        verbose_name = u'地址管理'
        verbose_name_plural = u'地址管理'

    def __unicode__(self):
        return str('')

class Point_Records(models.Model):
    TYPE = (
            ('product_show',u'产品秀积分'),
            ('review',u'评论奖励积分'),
            ('feedback',u'互动反馈积分'),
            ('promoting',u'推广奖励积分'),
            ('register',u'注册赠送积分'),
            ('order',u'购物赠送积分'),
            ('affiliate',u'佣金兑换积分'),
            ('compensation',u'订单补偿积分'),
        )

    STATUS = (
            ('activated', u'activated'),
            ('pending', u'pending'),
        )

    customer = models.ForeignKey(Customers)
    amount = models.IntegerField(default=0,blank=True, verbose_name=u"积分")
    type = models.CharField(max_length=100, choices=TYPE, default='product_show',blank=True,null=True, verbose_name=u"积分类型")
    status = models.CharField(max_length=20, choices=STATUS, default='activated',blank=True,null=True, verbose_name=u"状态")
    # order = models.ForeignKey(Order,default='', null=True, blank=True)
    order_id = models.IntegerField(default=0, null=True, blank=True)
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=0, blank=True, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'积分记录'
        verbose_name_plural = u'积分记录'

    def __unicode__(self):
        return str(self.id)

class Point_Payments(models.Model):
    customer = models.ForeignKey(Customers)
    amount = models.IntegerField(default=0,blank=True, verbose_name=u"积分数量")
    # order = models.ForeignKey(Order)
    order_id = models.IntegerField(default=0, null=True, blank=True)
    order_date = UnixDateTimeField(blank=True, null=True,verbose_name=u"下单日期")
    order_num = models.CharField(max_length=100, default='', blank=True , null=True, verbose_name=u"订单号")
    note = models.TextField(default='', blank=True, null=True, verbose_name=u"备注信息")

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=0, blank=True, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'积分使用记录'
        verbose_name_plural = u'积分使用记录'

    def __unicode__(self):
        return str('')

class Wishlists(models.Model):
    product = models.ForeignKey(Product)
    name = models.CharField(max_length=255,default='',null=False)
    created = UnixDateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    permalink = models.CharField(max_length=255,default='',null=False)
    thumbmail = models.CharField(max_length=255,default='',null=False)
    customer = models.ForeignKey(Customers)
    product_sku = models.CharField(max_length=100,default='',null=False)
    is_mailed = models.IntegerField(default=0,null=False)
    class Meta():
        verbose_name = u'wishlists'
        verbose_name_plural = u'wishlists' 

class Newsletters(models.Model):
    email = models.EmailField(default='', verbose_name=u"邮箱")
    created = UnixDateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    active = models.BooleanField(default=False,)
    firstname = models.CharField(max_length=100,default='',blank=True,null=True,)
    lastname = models.CharField(max_length=100,default='',blank=True,null=True,)
    gender = models.CharField(max_length=50,default='',blank=True,null=True,verbose_name=u'性别')
    zip = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'zipcode')
    occupation = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'职业')
    birthday = UnixDateTimeField(blank=True,null=True,verbose_name=u'生日')
    country = models.CharField(max_length=255,default='',blank=True,null=True,verbose_name=u'国家')

    class Meta():
        verbose_name = u'订阅用户'
        verbose_name_plural = u'订阅用户'

class Token(models.Model):
    customer = models.ForeignKey(Customers)
    created = UnixDateTimeField()
    token = models.CharField(max_length=40)
    site_id = models.IntegerField(default=1)