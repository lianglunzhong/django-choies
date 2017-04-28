# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from products.models import Product
from django.contrib.auth.models import User
from django.db import models
from products.models import Product
import phpserialize
from django_unixdatetimefield import UnixDateTimeField
from django.contrib import messages
from products.models import Category,Set,Productitem
from django.db import IntegrityError, transaction
import datetime
class CartItem(models.Model):
    customer = models.ForeignKey('accounts.Customers', null=True, blank=True)
    # variant = models.ForeignKey('products.Variant',default="", blank=True, null=True)
    item = models.ForeignKey(Productitem,default="", blank=True, null=True)
    qty = models.IntegerField(default=1)

    key = models.CharField(max_length=40, default="", blank=True, null=True)
    note = models.TextField(default="", blank=True, null=True)
    is_cart = models.IntegerField(default=1,verbose_name=u'1:购物车,0:save for later')

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True)
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = u'购物车产品'
        verbose_name_plural = u'购物车产品'


def get_symbol(currency):
    return settings.CURRENCIES[currency]['symbol']

def set_currency(value=0.0, currency='USD', base_currency='USD'):
    CURRENCIES = settings.CURRENCIES
    default_currency = base_currency
    value = value / CURRENCIES[default_currency]['factor'] * CURRENCIES[currency]['factor'] 
    value = (round(value, 2))
    return value 

def do_currency(value=0.0, currency='USD'):
    base_currency = settings.DEFAULT_CURRENCY
    return set_currency(value=value, currency=currency, base_currency=base_currency)

class Shipping(models.Model):
    OFF = (
            (1.0,'100%'),
            (0.9,'90%'),
            (0.8,'80%'),
            (0.7,'70%'),
            (0.6,'60%'),
            (0.5,'50%'),
            (0.45,'45%'),
            (0.4,'40%'),
            )
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    brief = models.TextField(default="", blank=True)
    link = models.CharField(max_length=300, default="", blank=True)
    orderby = models.IntegerField(default=1000)
    active = models.BooleanField(default=True)
    default = models.BooleanField(default=False)
    price = models.FloatField(default=0.0)
    off = models.FloatField(default=1.0, choices=OFF)

    def get_price(self, currency="USD", country="US", weight=0.0):
        weight = float(weight)
        if weight == 0.0 :
            return 0.0

        try:
            country = Country.objects.filter(code=country)
            shipping_zone = ShippingZone.objects.filter(shipping=self).filter(countries__in=country).get()
            shipping_price = ShippingPrice.objects.filter(shipping_zone=shipping_zone).filter(weight__lte=weight).order_by('-weight')[0]
            price = shipping_price.price + float(weight-shipping.weight) * float(shipping_price.offset_price) 
        except:
            price = self.price

        price = price * self.off
        # rmb转换成美元
        price = set_currency(price, settings.DEFAULT_CURRENCY , 'RMB')
        price = do_currency(price, currency)
        return price

    def __unicode__(self):
        return "%s|%s" % (self.name, self.label)

class Cart:
    def __init__(self, request):
        self.request = request

    def count(self):
        cart_items = self.get_cart_items()
        count = 0
        for cart_item in cart_items:
            count = count + cart_item.qty
        return count

    # 用户未登陆的时候，用来存储标示db中的产品是这个用户的，登陆后用user_logged_in signal 来更新CartItem.user
    def get_key(self):
        if self.request.session.get('cart_key'):
            key = self.request.session.get('cart_key')
        else:
            key = self.request.session.session_key
            self.request.session['cart_key'] = key
        return key

    def get_cart_items(self):
        if self.request.user.is_authenticated():
            cart_items = CartItem.objects.filter(user=self.request.user)
        else:
            cart_items = CartItem.objects.filter(key=self.get_key())

        return cart_items
    
    def in_stock(self):
        cart_items = self.get_cart_items()
        in_stock = True
        for cart_item in cart_items:
            if cart_item.item.qty < cart_item.qty:
                in_stock = False
                break

        return in_stock

    def get_item_total(self):
        currency = self.get_currency()
        item_total = 0.0
        for cart_item in self.get_cart_items():
            try:
                item_total += cart_item.qty * cart_item.item.get_price(currency=currency, qty=self.get_item_count(cart_item.item.product))
            except:
                # TODO
                pass
        return item_total

    def get_item_count(self, product):
        cart_items = self.get_cart_items()
        cart_items = cart_items.filter(item__product=product).all()
        count = 0
        for cart_item in cart_items:
            count = count + cart_item.qty

        return count

    def clear(self):
        # clean cart items
        cart_items = self.get_cart_items()
        cart_items.delete()

        try:
            del self.request.session['cart_coupon']
        except KeyError:
            pass

        try:
            del self.request.session['cart_shipping']
        except KeyError:
            pass

        try:
            del self.request.session['cart_shipping_address']
        except KeyError:
            pass

        try:
            del self.request.session['cart_payment']
        except KeyError:
            pass

        try:
            del self.request.session['cart_points']
        except KeyError:
            pass

    def get_promotion(self):
        now = datetime.datetime.now()
        promotions = Promotions.objects.filter(status=True).filter(start_time__lte=now).filter(end_time__gte=now).order_by('orderby')
        for promotion in promotions:
            if promotion.type == 0:
                if promotion.condition_value <= self.get_item_total():
                    return promotion
            elif promotion.type == 1:
                if promotion.condition_value <= self.count():
                    return promotion
        return None

    def get_promotion_amount(self):

        promotion = self.get_promotion()

        # no promotion
        if not promotion:
            return 0.00

        currency = self.get_currency()

        # percent
        if promotion.action_type == 0:
            amount = (promotion.value - 1.00) * self.get_item_total()
        # discount
        elif promotion.action_type == 1:
            # TODO
            amount = 0.00 - promotion.get_price(currency=currency)
        # free shipping
        elif promotion.action_type == 2:
            amount = 0.00 - self.get_shipping_price()
        # pre discount
        elif promotion.action_type == 3:
            amount = 0.00 - promotion.get_price(currency=currency) * self.count()
        else:
            amount = 0.00
        
        return round(amount, 2)

    def get_total(self):
        total = 0.0
        total = self.get_item_total() + self.get_shipping_price() + self.get_promotion_amount() + self.get_coupon_amount() + self.get_points_amount()
        return total

    def get_weight(self):
        weight = 0.0
        for cart_item in self.get_cart_items():
            weight += cart_item.qty * cart_item.item.get_weight()

        return weight
    
    def set_item(self, key, qty):
        key = int(key) if key.isdigit() else 0
        item = CartItem.objects.get(id=key)
        qty = int(qty)
        if qty > 0:
            item.qty = qty
            item.save()
        else:
            item.delete()

    def add_item(self, item, qty, note="", comment=""):
        if self.request.user.is_authenticated():
            item, is_created = CartItem.objects.get_or_create(item=item, user=self.request.user, note=note, comment=comment)
        else:
            item, is_created = CartItem.objects.get_or_create(item=item, key=self.get_key(), user=None, note=note, comment=comment)

        item.qty += qty
        item.save()
    
    def get_country(self):
        shipping_address = self.get_shipping_address()
        if shipping_address:
            return shipping_address.shipping_country
        else:
            return 'US'

    def get_shipping_price(self):
        currency = self.get_currency()
        shipping = self.get_shipping()
        return shipping.get_price(currency=currency, country=self.get_country(), weight=self.get_weight())

    def get_currency(self):
        return self.request.session.get('currency', settings.DEFAULT_CURRENCY)

    def get_comment(self):
        return self.request.session.get('cart_comment', '')

    def set_comment(self, data):
        self.request.session['cart_comment'] = data 

    def get_comment1(self):
        return self.request.session.get('cart_comment1', '')

    def set_comment1(self, data):
        self.request.session['cart_comment1'] = data 

    def get_shipping(self):
        id = self.request.session.get('cart_shipping', 0)
        try:
            shipping = Shipping.objects.get(id=id)
        except:
            shipping = Shipping.objects.get(default=True)
        return shipping

    def set_shipping(self, id):
        self.request.session['cart_shipping'] = id

    def set_points(self, points):
        self.request.session['cart_points'] = points

    def get_points(self):
        return self.request.session.get('cart_points', 0)

    def get_points_amount(self):
        currency = self.get_currency()
        points = self.get_points()
        amount = -0.01 * points
        return do_currency(amount, currency)

    def set_coupon(self, id):
        self.request.session['cart_coupon'] = id

    def get_coupon(self):
        id = self.request.session.get('cart_coupon', 0)
        try:
            coupon = Coupons.objects.get(id=id)
            print 'get_coupon'
            if coupon.enable_type == 0:
                return coupon
            elif coupon.enable_type == 1:
                if coupon.enable_value <= self.get_item_total():
                    print 'get_coupon 1'
                    return coupon
            elif coupon.enable_type == 2:
                if coupon.enable_value <= self.count():
                    return coupon
            else:
                pass
        except:
            return None

    def get_coupon_amount(self):
        print 'get_coupon_amount'
        coupon = self.get_coupon()

        # no coupon
        if not coupon:
            return 0.00

        currency = self.get_currency()

        # percent
        if coupon.action_type == 0:
            amount = (coupon.action_value - 1.00) * self.get_item_total()
        # discount
        elif coupon.action_type == 1:
            # TODO
            amount = 0.00 - coupon.get_price(currency=currency)
        # free shipping
        elif coupon.action_type == 2:
            amount = 0.00 - self.get_shipping_price()
        else:
            amount = 0.0

        
        return round(amount, 2)

    def get_shipping_address(self):
        id = self.request.session.get('cart_shipping_address', 0)
        try:
            address = ShippingAddress.objects.get(id=id, user=self.request.user)
        except:
            try:
                address = ShippingAddress.objects.filter(user=self.request.user)[0]
            except:
                return None

        return address

    def set_shipping_address(self, id):
        self.request.session['cart_shipping_address'] = id

    def get_payment(self):
        id = self.request.session.get('cart_payment', 0)
        try:
            payment = Payment.objects.get(id=id)
        except:
            payment = Payment.objects.get(default=True)
        return payment

    def set_payment(self, id):
        self.request.session['cart_payment'] = id

#class ShippingZone(models.Model):
#    name = models.CharField(max_length=100, unique=True)
#    shipping = models.ForeignKey(Shipping)
#    countries = models.ManyToManyField(Country, null=True, blank=True)
#
#    def __unicode__(self):
#        return self.name
#
#class ShippingPrice(models.Model):
#    weight = models.FloatField(default=0.0)
#    price = models.FloatField(default=0.0)
#    offset_price = models.FloatField(default=0.0)
#    shipping_zone = models.ForeignKey(ShippingZone)
#
#    class Meta:
#        unique_together = ('weight', 'shipping_zone',)
#
#    def __unicode__(self):
#        return str(self.id)

#def update_items(sender, instance, **kwargs):
#    if kwargs['action'] in ['post_add', 'post_remove', 'post_clear']:
#    #if kwargs['action'] in ['post_save', 'post_add',] and kwargs["model"] == Option:
#        print instance
#        print kwargs['action']
#        print kwargs.items()
#
##m2m_changed.connect(update_items, sender=Product.colors.through)
#m2m_changed.connect(update_items, sender=Product.categories.through)
##m2m_changed.connect(update_items, sender=Product.sizes.through)

class Cpromotions(models.Model):
    name=models.CharField(max_length=255,default='',verbose_name=u'名称',null=True)
    # site_id=models.IntegerField(default=1,null=True)
    conditions=models.TextField(null=True,verbose_name=u'促销条件')
    brief=models.TextField(null=True,verbose_name=u'简介')
    actions=models.TextField(null=True,verbose_name=u'促销方式')
    is_active=models.IntegerField(default=1,null=True)
    from_date=UnixDateTimeField(verbose_name=u'起始时间')
    to_date=UnixDateTimeField(verbose_name=u'截止时间')
    priority=models.IntegerField(default=0,verbose_name=u'优先级',blank=False)
    stop_further_rules=models.IntegerField(default=1,blank=False)
    restrictions=models.TextField(null=True,verbose_name=u'分类/产品限制')
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')
    celebrity_avoid=models.IntegerField(default=0,null=True,verbose_name=u'红人过滤')
    de=models.CharField(max_length=255,default='',verbose_name=u'DE简介',blank=True,)
    es=models.CharField(max_length=255,default='',verbose_name=u'ES简介',blank=True,)
    fr=models.CharField(max_length=255,default='',verbose_name=u'FR简介',blank=True,)
    #ru=models.CharField(max_length=255,default='')
    #pt=models.CharField(max_length=255,default='')

    def cpromotions(self,request):
        # 分类/产品限制
        is_restrict = request.POST.get('is_restrict')
        #促销条件
        conditions = request.POST.get('conditions')
        # 促销方式
        promotion_method = request.POST.get('promotion_method')

        brief = request.POST.get('brief')
        priority = request.POST.get('priority')
        # stop_further_rules = request.POST.get('stop_further_rules')#老后台页面仅获取页面传来的值，但没有数据操作
        celebrity_avoid = request.POST.get('celebrity_avoid')

        insert_restrict= 0
        insert_conditions= 0
        insert_actions= 0
        #分类/产品限制
        if is_restrict:
            restrictArr = {}
            restrictions = request.POST.get('restrictions')
            if restrictions == 'restrict_catalog':
                restrict = request.POST.get('restrict_catalog')
                restrict =  restrict.split()
                if len(restrict) != 0:
                    insert_restrict = 1
                    restrictArr[restrictions] = restrict
            elif restrictions == 'restrict_product':
                restrict = request.POST.get('restrict_product')
                restrict = restrict.split()
                if len(restrict) != 0:
                    insert_restrict = 1
                    restrictArr[restrictions] = restrict
            restrictArr = phpserialize.dumps(restrictArr)
            if not insert_restrict:
                messages.error(request, u'分类/产品限制不能为空')
        else:
            insert_restrict = 1
            restrictArr = None

        #促销条件
        if conditions == 'sum':
            sums = request.POST.get('sum')
            if len(sums) != 0:
                insert_conditions = 1
                conditions = 'sum:'+sums
        elif conditions == 'quantity':
            quantitys = request.POST.get('quantity')
            if len(quantitys) != 0:
                insert_conditions = 1
                conditions = 'quantity:'+quantitys
        elif conditions == 'whatever':
            insert_conditions = 1
        else:
            messages.error(request, u'促销方式不能为空')
        #促销方式
        #打折
        if promotion_method == 'discount':
            # 打折类型
            discount_method = request.POST.get('discount_method')
            promotion_set = {}
            promotion_set['action'] = promotion_method
            if discount_method == 'rate':
                rate = request.POST.get('rate')
                if len(rate) != 0:
                    insert_actions = 1
                    promotion_set['details'] = 'rate:'+rate
            elif discount_method == 'reduce':
                reduce = request.POST.get('reduce')
                if len(reduce) != 0:
                    insert_actions = 1
                    promotion_set['details'] = 'reduce:'+reduce
            actions = phpserialize.dumps(promotion_set)
            if not insert_actions:
                # actions = None
                messages.error(request, u'打折内容不能为空')
        #赠品
        elif promotion_method == 'largess':
            promotion_set = {}
            promotion_set['action'] = promotion_method
            promotion_qty = {}
            sku = request.POST.get('larges_SKU')
            sku = sku.split()

            if sku:
                product = Product.objects.filter(sku=sku[0]).first()
                if product:
                    proarr = {}
                    proarr['SKU'] = sku
                    proarr['id'] = product.id
                    proarr['price'] = request.POST.get('largess_price')
                    proarr['max_quantity'] = request.POST.get('largess_quantity')
                    proarrs = {}
                    proarrs[0] = proarr
                    promotion_qty['largesses'] = proarrs
                    promotion_qty['max_sum_quantity'] = request.POST.get('largess_sum_quantity')
                    promotion_set['details'] = promotion_qty
                    insert_actions = 1
                    actions = phpserialize.dumps(promotion_set)
                else:
                    messages.error(request,u'sku不存在')
            else:
                messages.error(request, u"sku不存在")

        #免运费
        elif promotion_method == 'freeshipping':
            promotion_set = {}
            promotion_set['action'] = promotion_method
            insert_actions = 1
            actions = phpserialize.dumps(promotion_set)
        #第二件半价
        elif promotion_method == 'secondhalf':
            promotion_set = {}
            promotion_set['action'] = promotion_method
            insert_actions = 1
            actions = phpserialize.dumps(promotion_set)
        #捆绑销售
        elif promotion_method == 'bundle':
            bundle_1 = 0
            bundle_2 = 0
            promotion_set = {}
            promotion_set['action'] = promotion_method
            promotionarr = promotion_set
            if request.POST.has_key('bundleprice'):
                bundleprice = request.POST.get('bundleprice')
                if len(bundleprice) != 0:
                    promotion_set['bundleprice'] = 'amt:'+bundleprice
                    bundle_1 = 1
                    promotionarr = promotion_set
            if request.POST.has_key('bundlenum'):
                bundlenum = request.POST.get('bundlenum')
                if len(bundlenum) != 0:
                    promotion_set['bundlenum'] = 'sum:'+bundlenum
                    bundle_2 = 1
                    promotionarr = promotion_set
            actions = phpserialize.dumps(promotionarr)
            #价格和件数都存在时，才保存数据
            if bundle_1 and bundle_2:
                insert_actions = 1
            if not insert_actions:
                messages.error(request, u'捆绑销售不能为空')
        else:
            messages.error(request, u'促销条件不能为空')
        if insert_restrict:
            self.restrictions = restrictArr
        if insert_conditions:
            self.conditions = conditions
        else:
            messages.error(request, u'促销条件不能为空')
        self.brief = brief
        if insert_actions:
            self.actions = actions
        # self.is_active = 1
        # self.stop_further_rules = stop_further_rules
        self.priority = priority
        #红人过滤
        self.celebrity_avoid = celebrity_avoid
        self.save()

    def __unicode__(self):
        return self.name

    def admin_save(self,request):
        admin_id = int(request.user.id)
        query = Cpromotions.objects.filter(id=self.id).update(admin=admin_id)

    class Meta:
        verbose_name = u'购物车促销'
        verbose_name_plural = u'购物车促销'

class Spromotions(models.Model):
    TYPE= (
            (0,u'vip'),        
            (1,u'daily'),
            (2,u'cost'),
            (3,u'outlet'),
            (4,u'special'),
            (5,u'activity'),
            (6,u'flash_sale'),
            (7,u'top_seller'),
            (-1,u'bomb'),
        )

    product = models.ForeignKey(Product)
    price = models.FloatField(default=0.0, verbose_name=u"促销价格")
    type = models.IntegerField(choices=TYPE, default=4,verbose_name=u"产品促销类型")
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')
    position = models.IntegerField(default=0,blank=True,null=True, verbose_name=u"排序")

    created = UnixDateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u"新增时间")
    expired = UnixDateTimeField(blank=True, null=True, verbose_name=u"过期时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否已删除")

    # def __unicode__(self):
    #     return self.id

    class Meta:
        verbose_name = u'特价产品促销'
        verbose_name_plural = u'产品促销'
    def save(self,*args,**kwargs):
        pro = Product.objects.filter(id=self.product_id).first()
        if self.price > pro.price:
            raise ValueError(u'促销价格不能大于本站产品价格')
        super(Spromotions,self).save(*args,**kwargs)
class Coupons(models.Model):
    TYPEUSE= (      
            (1,u'注册系统折扣'),
            (2,u'网站活动促销'),
            (3,u'批发佣金折扣'),
            (4,u'客服售后补偿'),
            (5,u'客服售前折扣'),
            (6,u'推广合作折扣'),
            (7,u'推广活动折扣'),
            (8,u'联盟优惠折扣'),
            (9,u'红人博客giveaway'),
            (10,u'404页面折扣号'),
            (11,u'购物车专属折扣(勿用)'),
            (12,u'测试单用'),
            (13,u'VIP 客户折扣'),
            (14,u'youtube红人专属折扣号'),
            (15,u'红人退款'),
            (16,u'EDM老客户维护'),
            (17,u'FB GIVEAWAY'),
            (18,u'polyvore contest'),
            (19,u'instagram首页'),
        )

    TYPE= (      
            (1,u'减折扣'),
            (2,u'减价'),
            (3,u'赠品'),
        )

    TARGET =(
            ('1',u"是"),
            ('0',u"否"),
        )

    ONSHOW =(
            (1,u"是"),
            (0,u"否"),
        )

    # site_id = models.BooleanField(default=True, verbose_name="Site id")
    code = models.CharField(max_length=255,verbose_name="code",unique=True)
    value = models.FloatField(default=0, verbose_name=u"金额")
    item_sku = models.CharField(max_length=30,blank=True, null=True,verbose_name="促销产品SKU",)
    type = models.IntegerField(choices=TYPE, default=0,verbose_name=u"折扣类型")
    target = models.CharField(max_length=50, choices=TARGET,blank=True,null=True, default=0,verbose_name="打折产品通用")
    on_show = models.IntegerField(choices=ONSHOW, default=0,verbose_name="是否为所有客户公用")
    limit = models.IntegerField(default=0,blank=True,null=True, verbose_name=u"可使用次数",help_text=u"(* 若次数值为 -1 则为无限使用！)" )
    effective_limit = models.IntegerField(default=0, verbose_name=u"对产品使用次数",help_text=u"只有限制类别或产品时有效(-1为不限制)")
    used = models.IntegerField(default=0, verbose_name=u"已使用次数")
    usedfor = models.IntegerField(choices=TYPEUSE,blank=True,null=True, default=0,verbose_name=u"折扣用途")
    product_limit = models.CharField(max_length=200,blank=True, null=True,verbose_name="产品限制",help_text=u"填入产品ID，多个ID以逗号分隔")
    catalog_limit = models.CharField(max_length=200,blank=True, null=True,verbose_name="分类限制",help_text=u"填入类别ID，多个ID以逗号分隔")
    condition = models.FloatField(default=0,blank=True,null=True, verbose_name=u"最低消费限制")
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')


    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    started = UnixDateTimeField(blank=True, null=True, verbose_name=u"开始时间")
    expired = UnixDateTimeField(blank=True, null=True, verbose_name=u"过期时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否已删除")
    is_mailed = models.BooleanField(default=0)
    def __unicode__(self):
        return self.code

    class Meta:
        verbose_name = u'折扣号'
        verbose_name_plural = u'折扣号'
    # 示例，raise ValueError admin会自动执行save方法
    # def save(self, *args,**kwargs):
    #     if self.code:
    #         coupon = Coupons.objects.filter(code=self.code).first()
    #         if coupon:
    #             raise ValueError(u'该code已存在，请重命名')
    #     super(Coupons,self).save(*args,**kwargs)

class CustomerCoupons(models.Model):
    # site_id = models.BooleanField(default=True, verbose_name="Site id")
    customer = models.ForeignKey('accounts.Customers')
    coupon = models.ForeignKey(Coupons) 

    created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True, blank=True, null=True,verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True, verbose_name=u"是否删除")

    def __unicode__(self):
        return str(self.id)

class Promotionfilter(models.Model):
    category = models.CharField(max_length=255,default=0,verbose_name=u'分类id')
    set = models.CharField(max_length=255,default=0,verbose_name=u'set id')
    price_lower = models.FloatField(default=0,verbose_name=u'最低价')
    price_upper = models.FloatField(default=0,verbose_name=u'最高价')


class Promotions(models.Model):
    # site_id = models.BooleanField(default=1)
    name = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name=u"Name")
    brief = models.TextField(blank=True, verbose_name=u"简介")
    filter = models.IntegerField(Promotionfilter,blank=True,null=True,default=0)
    actions = models.CharField(max_length=100, default='', blank=True, null=True)
    args = models.TextField(blank=True) 
    is_active = models.IntegerField(default=1) 
    is_view = models.IntegerField(default=1)
    from_date = UnixDateTimeField(verbose_name=u"开始时间")
    to_date = UnixDateTimeField(verbose_name=u"结束时间")
    order = models.IntegerField(default=0,blank=True, null=True,verbose_name=u"订单数")
    admin = models.ForeignKey(User,blank=True, null=True, verbose_name=u'Admin')  

    created = UnixDateTimeField(auto_now_add=True, verbose_name=u"创建时间")
    updated = UnixDateTimeField(auto_now=True,blank=True, null=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, blank=True,verbose_name=u"是否删除")

    category = models.ManyToManyField(Category,blank=True,verbose_name=u'分类id')
    set = models.ManyToManyField(Set,blank=True,verbose_name=u'set id')
    price_lower = models.FloatField(default=0,verbose_name=u'最低价')
    price_upper = models.FloatField(default=0,verbose_name=u'最高价')
    class Meta:
        verbose_name = u'新品折扣'
        verbose_name_plural = u'新品折扣'
    # promotions的actions字段数据保存
    def promotions(self, request):
        discount_method = request.POST.get('discount_method')
        action = ''
        if discount_method == 'rate':
            action = 'rate:'
            value = request.POST.get('rate')
            action += value
        elif discount_method == 'reduce':
            action = 'reduce:'
            value = request.POST.get('reduce')
            action += value
        elif discount_method == 'equal':
            action = 'equal:'
            value = request.POST.get('equal')
            action += value
        elif discount_method == 'points':
            action = 'points:'
            value = request.POST.get('points')

            action += value

        Promotions.objects.filter(id=self.id).update(actions = action)

    def __unicode__(self):
        return str(self.id)

    # promotions的filter字段保存promotionfilter的id,
    # 为了方便数据操作，把promotion的 category set price_lower price_upper字段在promotions表添加数据，
    # 得到数据后，保存到promotionfilter，得到promotionfilter的id，id保存到promotions的filter字段
    def promotionfilter(self):
        promotion = Promotions.objects.filter(id=self.id).first()
        category = promotion.category.all()
        set = promotion.set.all()

        category_str = ''
        set_str = ''
        for data in category:
            category_str += str(data.id)
            category_str += ','
        for data in set:
            set_str += str(data.id)
            set_str += ','
        category_str = category_str.strip(',')
        set_str = set_str.strip(',')

        if promotion.filter:
            Promotionfilter.objects.filter(id=promotion.filter).update(category=category_str,set=set_str,price_lower=promotion.price_lower,price_upper=promotion.price_upper)
        else:
            promotionfilter = Promotionfilter.objects.create(category=category_str, set=set_str,price_lower=promotion.price_lower, price_upper=promotion.price_upper)
            if promotionfilter.id:
                Promotions.objects.filter(id=self.id).update(filter=promotionfilter.id)




