# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django_unixdatetimefield import UnixDateTimeField
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import os
import accounts
import orders
# from accounts.models import Customers



class Celebrits(models.Model):
    SEX = (
            (0,'MALE'),
            (1,'FEMALE'),
            (2,'OTHER'),
        )

    name = models.CharField(max_length=100, default='', blank= True,verbose_name=u'姓名')
    email = models.CharField(max_length=100, default='', blank= True,verbose_name=u'邮箱')
    #customer = models.IntegerField(blank=True, verbose_name=u'customer_id')
    customer = models.ForeignKey('accounts.Customers',blank=True, null=True,verbose_name=u'用户ID')
    # country = models.ForeignKey(Country, blank=True, null=True, verbose_name=u'国家')
    country = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'国家')
    sex = models.IntegerField(choices=SEX, default=1, verbose_name=u"性别")
    birthday = UnixDateTimeField(blank=True, null=True,  verbose_name=u"生日")
    level = models.IntegerField(default=0, verbose_name=u"会员等级")
    admin = models.ForeignKey(User, blank=True, null=True, verbose_name=u'Admin')

    created = UnixDateTimeField(auto_now_add=True, blank=True,null=True,verbose_name=u"新增时间")
    updated = UnixDateTimeField(auto_now=True, blank=True,null=True,verbose_name=u"修改时间")

    is_able = models.BooleanField(default=True)
    remark = models.TextField(default=0,blank=True,null=True)
    show_name = models.CharField(max_length=100, default='', blank=True,null=True, verbose_name=u'显示名称')

    height = models.CharField(max_length=50, blank=True,null=True, default='', verbose_name=u"身高", help_text=u"单位cm")
    weight = models.CharField(max_length=50, blank=True,null=True,default='', verbose_name=u"体重", help_text=u"单位kg")
    bust = models.CharField(max_length=50, blank=True,null=True, default='', verbose_name=u"胸围", help_text=u"单位cm")
    waist = models.CharField(max_length=50, blank=True,null=True, default='', verbose_name=u"腰围", help_text=u"单位cm")
    hips = models.CharField(max_length=50, blank=True,null=True, default='', verbose_name=u"臀围", help_text=u"单位cm")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name =  u'红人'
        verbose_name_plural = u'红人'

class CelebrityBlogs(models.Model):

    TYPE = (
            ('blog',u'Blog'),
            ('lookbook',u'Lookbook'),
            ('facebook',u'Facebook'),
            ('youtube',u'Youtube'),
            ('polyvore',u'Polyvore'),
            ('twitter',u'Twitter'),
            ('pinterest',u'Pinterest'),
            ('other',u'Other'),
        )

    celebrity = models.ForeignKey(Celebrits, blank=True, null=True, verbose_name=u'红人ID')
    celebrity_email = models.CharField(max_length=100, default='', blank= True, verbose_name=u'红人邮箱')
    type = models.CharField(max_length=100,choices=TYPE, default=0,blank=True,null=True, verbose_name=u'博客类型')
    url = models.CharField(max_length=255, default='', blank=True, verbose_name=u'博客链接')
    profile = models.IntegerField(default=0, blank=True,null=True)
    flow = models.IntegerField(default=0, blank=True,null=True)

    def __unicode__(self):
        return ''


class CelebrityFees(models.Model):
    celebrity = models.ForeignKey(Celebrits, blank=True, null=True, verbose_name=u'红人ID')
    email = models.CharField(max_length=100, default='', blank= True, verbose_name=u'红人邮箱')
    fee = models.FloatField(default=0.0, blank=True, verbose_name=u'Fee')
    currency = models.CharField(max_length=50, default='USD', blank=True, verbose_name="币种")
    pp_account = models.CharField(max_length=100, default='', blank=True, verbose_name=u'PP Account')
    admin = models.ForeignKey(User,verbose_name='Admin')
    what_for=models.CharField(max_length=100, default='', blank=True,null=True, verbose_name=u'What for')
    created = UnixDateTimeField(auto_now_add=True, blank=True,null=True,verbose_name='Created')
    updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"Updated")

    def __unicode__(self):
        return self.fee


class CelebrityOrder(models.Model):
    celebrity = models.ForeignKey(Celebrits, blank=True, null=True, verbose_name=u'红人ID')
    order = models.ForeignKey('orders.Order', blank=True, null=True, verbose_name=u'订单ID')
    ordernum = models.CharField(max_length=100, blank=True, default='', verbose_name=u'订单号')
    sku = models.CharField(max_length=100, blank=True, default='', verbose_name=u'SKU')
    url = models.CharField(max_length=255, blank=True, default='', verbose_name=u'URL')
    show_date = UnixDateTimeField(blank=True,null=True, verbose_name='Show Date')

    def __unicode__(self):
        return self.id

class CelebrityContacted(models.Model):
    celebrity = models.ForeignKey(Celebrits, blank=True, null=True, verbose_name=u'红人ID')
    email = models.CharField(max_length=100, default='', blank=True, verbose_name=u'Email')
    sites = models.TextField(default='', blank=True, verbose_name=u'Sites')
    admin = models.ForeignKey(User, verbose_name='Admin')
    created = UnixDateTimeField(auto_now_add=True, verbose_name='Created')

    def __unicode__(self):
        return self.id



class CelebrityBackups(models.Model):
    GENDER = (
            (0,'MALE'),
            (1,'FEMALE'),
            (2,'OTHER'),
        )
    email = models.CharField(max_length=100, default='', blank=True, verbose_name=u'Email')
    sites = models.TextField(default='', blank=True, verbose_name=u'Sites')
    gender = models.IntegerField(default=1, blank=True,null=True, verbose_name=u'Gender')
    country = models.CharField(max_length=100, default='', blank=True, verbose_name=u'Country')
    comment = models.TextField(default='', blank=True,null=True, verbose_name=u'Comment')
    created = UnixDateTimeField(auto_now_add=True, verbose_name='Created')
    is_join = models.BooleanField(default=True)
    assign = models.IntegerField(default=0,blank=True,null=True)

    def __unicode__(self):
        return self.id

class Lookbooks(models.Model):
    title = models.CharField(null=True,max_length=255,verbose_name='标题')
    images = models.TextField(null=True,verbose_name='图片名')
    created = models.IntegerField(null=True,verbose_name='创建时间')
    visibility = models.IntegerField(null=True,verbose_name='是否可见')

class Lookbook_reviews(models.Model):
    lookbook = models.ForeignKey(Lookbooks,verbose_name='looksbooks_id')
    customer = models.ForeignKey('accounts.Customers',verbose_name='customer_id')
    content = models.TextField(null=True,verbose_name='评论内容')
    star = models.IntegerField(null=True,verbose_name='星级')
    types = models.IntegerField(null=True,verbose_name='0:lookbook; 1:product;')
    created = models.IntegerField(null=True,verbose_name='创建时间')

class Flows(models.Model):
    celebrity = models.ForeignKey(Celebrits,verbose_name='celebrits_id')
    types = models.CharField(max_length=50,null=True,verbose_name='数据来源')
    name = models.CharField(max_length=100,null=True,verbose_name='sku')
    flow = models.IntegerField(null=True,verbose_name='次数')