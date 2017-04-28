# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from mptt.models import MPTTModel
import datetime
import time
import re
from django.db.models import Avg
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Sum
from django_unixdatetimefield import UnixDateTimeField
from django.conf import settings
from uuslug import slugify
import os
import accounts
from products.models import Product,ProductImage,Productitem
from core.models import Country
from carts.models import Coupons

class Order(models.Model):
    ORDER_STATUS = (
            (0, u'Unpaid'),
            (1, u'Fail'),
            (2, u'Paid'),
            (3, u'Processing'),
            (4, u'Shipping'),
            (5, u'Shipped'),
            (6, u'Canceled'),
            (7, u'Delete'),
        )

    PAYMENT_STATUS = (
            ('new', u'New [New Order]'),
            ('new_s', u'New_s'),
            ('success', u'Success [Success]'),
            ('pending', u'Pending [Pending]'),
            ('failed', u'Failed [Failed]'),
            ('cancel', u'Cancel [Cancel]'),
            ('partial_paid', u'Partial Pail [Partial Pail]'),
            ('repeat_pay', u'Repeat Pay [Globelill method repeat pay]'),
            ('verify_failed', u'Failed [Not pass verific ation]'),
            ('verify_banned', u'Faild [Banned List]'),
            ('verify_pass', u'Success [Pay success and pass verific ation]'),
        )

    SHIPPING_STATUS = (
            ('news', u'New Order'),
            ('new_s', u'New_s'),
            ('pre_o', u'Pre Order'),
            ('processing', u'Processing'),
            ('partial_shipped', u'Partial Shipped'),
            ('shipped', u'Shipped'),
            ('delivered', u'Delivered'),
            ('pickup', u'Pick Up'),
        )

    REFUND_STATUS = (
            ('prepare_refund', u'Prepare refund'),
            ('partial_refund', u'Partial refund'),
            ('refund', u'Refund'),
        )
    MOBILE_ORDER = (
            (1,u'YES'),
            (0,u'NO'),
        )
    IS_REMARK = (
            (1,u'YES'),
            (0,u'NO'),
        )


    parent = models.ForeignKey('self', null=True, blank=True)
    # site_id = models.BooleanField(default=True, verbose_name=u"Site id")
    erp_header_id = models.IntegerField(default=0, blank=True, null=True)
    erp_customer_id = models.IntegerField(default=0, blank=True, null=True)
    erp_fee_line_id = models.IntegerField(choices=MOBILE_ORDER,db_index=True, default=0, blank=True, null=True, verbose_name=u'手机订单') #手机订单为1 
    erp_otherfee_line_id = models.IntegerField(default=0, blank=True, null=True)
    erp_ship_line_id = models.IntegerField(default=0, blank=True, null=True)

    customer = models.ForeignKey('accounts.Customers', blank=True , null=True)
    email = models.EmailField(default='', blank=True , null=True, verbose_name=u"电子邮件")

    ordernum = models.CharField(max_length=100,unique=True, default='', blank=True , null=True, verbose_name=u"订单号")
    status = models.IntegerField(choices=ORDER_STATUS, default=0, blank=True, null=True, verbose_name=u"订单状态")
    products = models.TextField(default='', blank=True, null=True, verbose_name=u"产品信息")

    amount_products = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"产品总价")
    amount_shipping = models.FloatField(default=0.0, blank=True ,null=True, verbose_name=u"运费")
    amount_order = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"订单总额")
    coupon_code = models.CharField(max_length=255, blank=True, null=True, default='', verbose_name=u"折扣号")
    amount_coupon = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"折扣金额")
    amount_point = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"使用积分")
    amount_drop_shipping = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"amount_drop_shipping")
    amount = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"合计")
    amount_refund = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"退款金额")

    currency = models.CharField(max_length=8, default='USD', blank=True,null=True, verbose_name=u"币种")
    rate = models.FloatField(default=1.0, blank=True, null=True, verbose_name=u'对美元汇率') 
    
    amount_payment = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"支付金额")
    currency_payment = models.CharField(max_length=8, default='', blank=True, null=True, verbose_name=u"支付币种")
    rate_payment = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u'支付汇率')
    # payment_status = models.IntegerField(choices=PAYMENT_STATUS, default=0, verbose_name=u"支付状态")
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=255, null=True, default='new', blank=True, verbose_name=u"支付状态")
    # transaction_id = models.CharField(max_length=60, unique=True, blank=True, default='', verbose_name=u"交易号")
    transaction_id = models.CharField(max_length=60, blank=True, null=True, default='', verbose_name=u"交易号")
    payment_date = UnixDateTimeField(blank=True, null=True,  verbose_name=u"支付时间")
    verify_date = UnixDateTimeField(blank=True, null=True,  verbose_name=u"确认时间")

    #shipping_status = models.IntegerField(choices=SHIPPING_STATUS, default=0, verbose_name=u"发货状态")
    shipping_status = models.CharField(choices=SHIPPING_STATUS , max_length=255, default='new', blank=True, null=True, verbose_name=u"发货状态")
    shipping_method = models.CharField(max_length=100, null=True, default='', blank=True, verbose_name=u"发货方式")
    shipping_weight = models.FloatField(default=0.0, null=True, blank=True, verbose_name=u"快递重量")
    shipping_code = models.CharField(max_length=100, null=True, default='', blank=True, verbose_name=u"物流号码")
    shipping_url = models.CharField(max_length=100, null=True, default='', blank=True, verbose_name=u"查询网址")
    shipping_comment = models.TextField(null=True, default='', blank=True, verbose_name=u"备注信息")
    shipping_date = UnixDateTimeField(blank=True,db_index=True, null=True, verbose_name=u"发货日期")

    created = UnixDateTimeField(auto_now_add=True, blank=True,db_index=True, null=True, verbose_name=u"下单日期")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"最后修改")

    ip = models.GenericIPAddressField(default='0.0.0.0', blank=True, null=True, verbose_name=u'IP地址')
    flag = models.CharField(max_length=100, default='', blank=True, null=True)

    shipping_firstname = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Shipping First Name')
    shipping_lastname = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Shipping Last Name')
    shipping_country = models.CharField(max_length=50, default='',db_index=True, blank=True, null=True, verbose_name=u'Shipping Country')
    shipping_state = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u'Shipping State/Province')
    shipping_city = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u'Shipping City')
    shipping_address = models.CharField(max_length=500, default='',blank=True, null=True, verbose_name=u'Shipping Address')
    shipping_zip = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Shipping Zip/Postal code')
    shipping_phone = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Shipping Home Phone')
    shipping_mobile = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Mobile')
    shipping_cpf = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'CPF')

    billing_firstname = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Billing First Name')
    billing_lastname = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Billing Last Name')
    billing_country = models.CharField(max_length=50, default='', blank=True, null=True, verbose_name=u'Billing Country')
    billing_state = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u'Billing State/Province')
    billing_city = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u'Billing City')
    billing_address = models.CharField(max_length=500, default='', blank=True, null=True, verbose_name=u'Billing Address' )
    billing_zip = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Billing Zip/Postal code')
    billing_phone = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'Billing Home Phone' )
    billing_mobile = models.CharField(max_length=100, default='', blank=True, null=True, )

    lang = models.CharField(max_length=30, blank=True, null=True, verbose_name=u"语言")

    # refund_status = models.IntegerField(choices=REFUND_STATUS, default=0, verbose_name=u"退款状态")
    refund_status = models.CharField(choices=REFUND_STATUS, max_length=255, default='', blank=True, null=True, verbose_name=u"退款状态")
    payment_method = models.CharField(max_length=50, null=True, default='', blank=True, verbose_name=u'付款方式')

    cc_num = models.CharField(max_length=20, default='', blank=True, null=True)
    cc_type = models.CharField(max_length=10, default='', blank=True, null=True)
    cc_cvv = models.CharField(max_length=10, default='', blank=True, null=True)
    cc_exp_month = models.CharField(max_length=10, default='', blank=True, null=True)
    cc_exp_year = models.CharField(max_length=10, default='', blank=True, null=True)
    # cc_exp_date = UnixDateTimeField(blank=True, null=True,)
    cc_issue = models.CharField(max_length=50, default='', blank=True, null=True)
    # cc_valid_date = UnixDateTimeField(blank=True, null=True,)
    cc_valid_month = models.CharField(max_length=10, default='', blank=True, null=True)
    cc_valid_year = models.CharField(max_length=10, default='', blank=True, null=True)


    promotions = models.TextField( default='', blank=True, null=True, verbose_name=u"Promotions")
    largesses =  models.TextField(default='', blank=True, null=True)
    drop_shipping = models.IntegerField(default=0, blank=True, null=True)
    payment_count = models.IntegerField(default=0, blank=True, null=True)
    points = models.IntegerField(default=0, blank=True, null=True)
    affiliate_id = models.IntegerField(default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True,db_index=True,)
    is_marked = models.IntegerField(choices=IS_REMARK,default=0, blank=True,verbose_name=u'异常单')

    referrer = models.CharField(max_length=255, blank=True, default='', null=True)
    deliver_time = UnixDateTimeField(blank=True, null=True,)
    is_verified = models.BooleanField(default=False)
    is_pre_order = models.BooleanField(default=False)
    email_status = models.IntegerField(blank=True, default=0, null=True)

    order_from = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u'订单来源')

    unprint_mail_flg = models.BooleanField(default=0, blank=True,)
    order_print_time = UnixDateTimeField(blank=True, null=True)
    order_remark =  models.IntegerField(default=0, blank=True, null=True)
    logistics_days = models.IntegerField(default=0, blank=True, null=True)
    order_insurance = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"运费险")

    facebook_cpc = models.BooleanField(default=0, blank=True,)
    source_league = models.CharField(max_length=100, default='', blank=True, null=True)

    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")
    

    _original_status = None

    class Meta:
        verbose_name = u'订单'
        verbose_name_plural = u'订单'

    @property
    def symbol(self):
        return get_symbol(self.currency)

    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self._original_status = self.status

    def item_count(self):
        count = 0
        items = OrderItem.objects.filter(order_id=self.id)
        for item in items:
            count += item.qty

        return count

    def orderpoints(self):
        points = 0
        order_items = OrderItem.objects.filter(order_id=self.id)
        for order_item in order_items:
            points += order_item.item.product.point

        return points

    def is_paid(self):
        if self.status in [0,1]:
            return False 
        else:
            return True

    def pay(self):
        if not self.is_paid():
            self.status = 2
            self.save()
            return True
        else:
            return False

    def fail(self):
        if not self.is_paid():
            self.status = 1
            self.save()
            return True
        else:
            return False

    def can_view(self):
        if self.status in [6,7]:
            return False
        else:
            return True

    def handle_stock(self):
        order_items = self.orderitem_set.all()
        for order_item in order_items:
            order_item.item.qty = order_item.item.qty - order_item.qty
            order_item.item.save()

    @models.permalink
    def get_absolute_urls(self):
        return ('order', (), {'ordernum':self.ordernum, })


    # def save(self, *args, **kw):
    #     super(Order, self).save(*args, **kw)
    #     # change order status unpaid, fail to paid:
    #     if self._original_status in [0, 1] and self.status == 2:
    #         PointLog.objects.create(user=self.user, order=self, points=self.points(), note="")

    def __unicode__(self):
        return str(self.id)

    def refund_message_save(self, request):
        refund_message = request.POST.get('refund_message')
        refund_status = request.POST.get('refund_status')
        
        if refund_status != self.refund_status:
            query_update = Order.objects.filter(id=self.id).update(refund_status=refund_status)
            basic_message = 'update refund_status from ' + str(self.refund_status) + ' to ' + str(refund_status)
            query_create = OrderHistories.objects.get_or_create(order_id=self.id, message=basic_message,order_status='update basic')
            if refund_message:
                query_create = OrderHistories.objects.get_or_create(order_id=self.id, message=refund_message,order_status='update statuc')
            
    def payment_message_save(self,request):
        payment_message = request.POST.get('payment_message')
        payment_status = request.POST.get('payment_status')
        
        if payment_status != self.payment_status:
            query_update = Order.objects.filter(id=self.id).update(payment_status=payment_status)
            basic_message = 'update payment_status from ' + str(self.payment_status) + ' to ' + str(payment_status)
            query_create = OrderHistories.objects.get_or_create(order_id=self.id, message=basic_message,order_status='update basic')
            if payment_message:
                query_create = OrderHistories.objects.get_or_create(order_id=self.id, message=payment_message,order_status='update statuc')


    def customer_fullname(self):
        name = accounts.models.Customers.objects.filter(id=self.customer_id).values_list('firstname','lastname')
        if name:
            fullname = name[0][0] + ' ' + name[0][1]
            return fullname
        else:
            return name

    def customer_created(self):
        created = accounts.models.Customers.objects.filter(id=self.customer_id).values_list('created')
        if created:
            return created[0][0]
        else:
            return 'none'

    def coupon_type(self):
        coupon_code = self.coupon_code
        coupon_type = u'None'
        if coupon_code:
            coupons = Coupons.objects.filter(code=str(coupon_code)).first()
            types = coupons.type
            if types == 1:
                coupon_type = u'减折扣'
            elif types == 2:
                coupon_type = u'减价'
            else:
                coupon_type = u'赠品'
        return coupon_type

    #订单产品添加
    def add_product(self,request):
        skus = []
        orderitems = OrderItem.objects.filter(order_id=self.id)
        for orderitem in orderitems:
            skus.append(orderitem.sku)
        print skus
        for sku in skus:
            name = ''
            product_id = ''
            item_id = ''
            link = ''
            cost = ''

            product = Product.objects.filter(sku=sku).first()
            if product:
                query = OrderItem.objects.filter(sku=sku,order_id=self.id).order_by('-id').update(name=product.name,product_id=product.id,item_id=product.id,cost=product.cost,link=product.link)



@receiver(post_save, sender=Order)
def order_update_ordernum(sender, instance, **kwargs):
    if not instance.ordernum:
        instance.ordernum = "%s%04d%08d" % (datetime.datetime.now().strftime("%y%m%d"), random.randint(0, 9999), instance.id)
        instance.save()

class OrderItem(models.Model):
    # site_id = models.BooleanField(default=1, blank=True)
    order = models.ForeignKey(Order, default='', null=True)
    product = models.ForeignKey(Product, default='', null=True)
    item = models.ForeignKey(Productitem, blank=True, null=True, verbose_name=u"item_id")
    name = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"Name")
    sku = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"SKU")
    link = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"URL")
    quantity = models.IntegerField(default=0, blank=True, null=True, verbose_name=u"数量")
    original_price = models.FloatField(default=0.0, blank=True, null=True,)
    price = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"Price")
    cost = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"Cost")
    is_gift = models.BooleanField(default=False, blank=True, verbose_name=u"Is_gift")
    weight = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"Weight")
    key = models.CharField(max_length=200, default='', blank=True, null=True,)
    customize_type = models.CharField(max_length=50, default='none', blank=True, null=True,)
    customize = models.CharField(max_length=50, default='', blank=True, null=True,)
    status = models.CharField(max_length=50, default='', blank=True, null=True, verbose_name=u'Status')

    tracking_number = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"运单号")
    tracking_link = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"物流查询地址")
    attributes = models.CharField(max_length=1000, default='', blank=True, null=True, verbose_name=u'Attributes')

    erp_line_id = models.IntegerField(default=0, blank=True, null=True)
    erp_line_status = models.CharField(max_length=255, default='', blank=True, null=True)
    custom_made = models.CharField(max_length=50, default='', blank=True, null=True)

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    @property
    def symbol(self):
        return get_symbol(self.currency)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = u'产品信息'
        verbose_name_plural = u'产品信息'

    def get_image_thumb(self):
        #images = self.Productimage_set.order_by('id').filter(deleted=False).first()
        images = ProductImage.filter(product_id=self.product_id).order_by('id').first()
        image_url = ''
        if images:
            image = str(images.image)
            if image:
                image_url = image
            else:
                image_name = str(images.id)+'.jpg'
                image_url = 'pimgs/pimages/'+image_name 
        return  image_url           

class OrderHistories(models.Model):
    # site_id = models.BooleanField(default=1, blank=True)
    order = models.ForeignKey(Order)
    order_status =models.CharField(max_length=64,default='', verbose_name=u"操作类型")
    admin = models.ForeignKey(User, blank=True, null=True, default=None, verbose_name="Admin")
    #item = models.ForeignKey(Item)
    message = models.TextField(default='', blank=True, null=True, verbose_name=u"备注信息")

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

class OrderMessages(models.Model):
    STATUS = (
        (1,u"是"),
        (0,u"否"),
    )

    order = models.ForeignKey(Order)
    message = models.TextField(default='', blank=True, null=True, verbose_name=u"备注信息")
    status = models.IntegerField(choices=STATUS, default=1, blank=True, null=True, verbose_name=u"是否可见")

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

class OrderPayments(models.Model):
    order = models.ForeignKey(Order, blank=True, null=True,)
    customer = models.ForeignKey('accounts.Customers', blank=True, null=True,)
    payment_method = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u"支付方式")
    trans_id = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"交易号")
    amount = models.FloatField(default=0.0, verbose_name=u"订单金额")
    currency = models.CharField(max_length=10, default='', blank=True, null=True, verbose_name=u"币种")
    comment = models.TextField(default='', blank=True, null=True, verbose_name=u"内容")
    #cache = models.CharField(max_length=300, default='', blank=True, null=True, verbose_name=u"交易号")
    payment_status = models.CharField(max_length=255, default='', blank=True, null=True)
    ip = models.CharField(max_length=20, blank=True, null=True, verbose_name="IP",)
    first_name = models.CharField(max_length=100, default='', blank=True,null=True)
    last_name = models.CharField(max_length=100, default='', blank=True,null=True)
    email = models.EmailField(default='', blank=True,null=True, verbose_name=u"客户邮箱")
    address = models.CharField(max_length=500, default='', blank=True, null=True)
    city = models.CharField(max_length=255, default='', blank=True, null=True)
    state = models.CharField(max_length=255, default='', blank=True, null=True)
    # country = models.ForeignKey('core.Country', null=True, blank=True)
    country = models.CharField(max_length=255, default='', blank=True, null=True)
    zip = models.CharField(max_length=100, default='', blank=True, null=True)
    phone = models.CharField(max_length=100, default='', blank=True, null=True)
    vip_status = models.IntegerField(default=0, blank=True, null=True, verbose_name=u"vip状态")

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = u'订单支付历史'
        verbose_name_plural = u'订单支付历史'


class OrderRemarks(models.Model):

    # site_id = models.BooleanField(default=1, blank=True)
    order = models.ForeignKey(Order)
    admin = models.ForeignKey(User, blank=True, null=True, verbose_name=u'Admin')
    remark = models.TextField(default='', blank=True, null=True, verbose_name=u"标记信息")
    type = models.IntegerField(default=1, verbose_name=u"是否可见")
    ip = models.CharField(max_length=20,verbose_name="IP",)

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = u'备注'
        verbose_name_plural = u'备注'

class OrderShipments(models.Model):
    IS_ERROR = (
            (1, u'是'),
            (0, u'否'),
        )

    admin = models.ForeignKey(User, blank=True, null=True, verbose_name=u'Admin')
    # site_id = models.BooleanField(default=1, blank=True)
    order = models.ForeignKey(Order, blank=True, null=True,)
    ordernum = models.CharField(max_length=100, blank=True, null=True, verbose_name=u"订单号")
    carrier = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u"物流") 
    tracking_code = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u"运单号")
    tracking_link = models.CharField(max_length=255, default='', blank=True, null=True, verbose_name=u"物流查询地址")
    ship_price = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"运费")
    ship_date = UnixDateTimeField(blank=True, null=True, verbose_name=u"发货时间")
    actual_weight = models.FloatField(default=0.0, blank=True, null=True, verbose_name=u"发货实称重量")
    is_error = models.IntegerField(choices=IS_ERROR, default=0, blank=True, null=True, verbose_name=u"追踪问题")
    package_id = models.IntegerField(default=0, blank=True, null=True,) 

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = u'发货信息'
        verbose_name_plural = u'发货信息'

class OrderShipmentitems(models.Model):

    order = models.ForeignKey(Order)
    shipment = models.ForeignKey(OrderShipments)
    item = models.ForeignKey(Product)
    quantity = models.IntegerField(default=1, blank=True,null=True, verbose_name=u"数量")

    created = UnixDateTimeField(auto_now_add=True, blank=True,null=True,  verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True,null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

    def get_ShipmentProductSKU(self):
        sku = Product.objects.filter(id=self.item).values_list('sku')
        return sku[0][0]

    def get_image_thumb(self):
        #images = self.Productimage_set.order_by('id').filter(deleted=False).first()
        images = ProductImage.filter(product_id=self.item_id,deleted=False).first()
        if images:
            image_url = str(images.image)
            image_url_array = image_url.split('/')
            url = '/'+image_url_array[0]+'/100/'+image_url_array[2]
        else:
            url = "/static/admin/img/100x100.png"

        return format_html(u'<img src="%s" />' % (url))



