#-*- coding: utf-8 -*-
from django.contrib import admin
from .models import Order,OrderItem,OrderShipments,OrderShipmentitems,OrderRemarks,OrderPayments,OrderHistories
import orders
import csv
from django.conf import settings
from datetime import datetime
from django.core.urlresolvers import reverse
from django.contrib.admin import SimpleListFilter
from django.shortcuts import render_to_response, get_object_or_404,redirect
import StringIO,csv
from django.conf.urls import url, include
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from core.views import write_csv
from products.models import ProductImage
from core.admin import SearchAdmin
import phpserialize
from django.contrib import messages
from lib.filters import UnionFieldListFilter,DoubleTextInputFilter
import time
class OrderHistoriesInline(admin.TabularInline):
    model = OrderHistories
    extra = 0
    max_num = 100
    can_delete = False

    def username(self,obj):
        output = ''
        if obj.admin:
            output += obj.admin.username

        return output
    username.allow_tags = True
    username.short_description = 'Admin'

    fields = ('order_status','username','message','created')
    readonly_fields = ('order_status','username','message','created')


class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0
    max_num = 20
    can_delete = True
    
    #产品图片预览图
    def OrderItemImage(self, obj):
        product_id = obj.product
        image_url = ''
        productimage = ProductImage.objects.filter(product_id=product_id).order_by('id').first()
        if productimage:
            image = str(productimage.image)
            if image:
                image_url = image
            else:
                image_name = str(productimage.id)+'.jpg'
                image_url = 'pimgs/pimages/'+image_name
        output1 = ""
        output1 += "/site_media/"+image_url

        output2 = ""
        output2 += "<img src='"+output1+"' height='100px' width='110px'"

        output3 = ""
        output3 += "<a href='"+output1+"' target='blank'>"+output2+"</a>"
        
        output = ""
        output += "<img src='/site_media/"
        output += image_url
        output += "' height='100px' width='110px'>" 
    OrderItemImage.allow_tags = True
    OrderItemImage.short_description = u'Image'

    # def OrderItemRemark(self, obj):
    #     output = obj.orderremarks.remark
    #     return output
    # OrderItemRemark.allow_tags = True
    # OrderItemRemark.short_description = u'Remark'

    fields = ['OrderItemImage', 'name', 'attributes','sku', 'original_price','price', 'quantity','cost','weight', 'status', 'is_gift', 'created',]
    readonly_fields=['OrderItemImage', 'name', 'original_price','cost','weight', 'status', 'is_gift', 'created','order',]


class OrderShipmentsInline(admin.TabularInline):

    model = OrderShipments

    extra = 0
    max_num = 20
    can_delete = False 

    def ShipmentItemImage(self, obj):
        output = orders.models.Ordershipmentitems.get_image_thumb()
        return output
    ShipmentItemImage.allow_tags = True
    ShipmentItemImage.short_description = 'Image'

    def ShipmentItemQty(self, obj):
        output = orders.models.Ordershipmentitems.quantity
        return output
    ShipmentItemQty.allow_tags = True
    ShipmentItemQty.short_description = 'QTY'

    def ShipmentItemSKU(self, obj):
        output = orders.models.Ordershipmentitems.get_ShipmentProductSKU()
        return output
    ShipmentItemSKU.allow_tags = True
    ShipmentItemSKU.short_description = u'SKU'

    fields = ['carrier', 'tracking_code', 'tracking_link', 'ship_price', 'ship_date','ShipmentItemImage','ShipmentItemSKU','ShipmentItemQty']
    readonly_fields = ['carrier', 'tracking_code', 'tracking_link', 'ship_price', 'ship_date','ShipmentItemImage','ShipmentItemSKU','ShipmentItemQty','ShipmentItemSKU','ShipmentItemQty', 'ShipmentItemImage']


class OrderPaymentsInline(admin.TabularInline):

    model = OrderPayments

    extra = 0
    max_num = 20
    can_delete = False 

    fields = ['payment_method','trans_id', 'amount','currency','comment','state','created',]
    readonly_fields = ['comment', 'state','created',]

class OrderRemarksInline(admin.TabularInline):

    model = OrderRemarks
    extra = 0
    max_num = 20
    can_delete = False

    fields = ['remark', 'admin', 'created', 'ip',]
    readonly_fields = [ 'admin', 'created', 'ip',]

class Filterbyday(SimpleListFilter):
    title = u'今天'
    parameter_name = 'created'

    def lookups(self, request, model_admin):
        supplier_type = []
        supplier_type.append([1, '今天所有的订单'])
        supplier_type.append([2, '今天支付成功的订单'])

        return supplier_type


    def queryset(self, request, queryset):
        import time
        now = time.time()
        midnight = now - (now % 86400) + time.timezone
       
        if self.value() == '1' :
            count = queryset.filter(created__gte=midnight).count()
            messages.success(request, u'今日订单，共 %s 单' % count)
            return queryset.filter(created__gte=midnight).all()
        elif self.value() == '2':
            status = ['verify_pass','success']
            count = queryset.filter(created__gte=midnight, payment_status__in=status).count()
            messages.success(request,u'今日订单，支付成功共 %s 单' % count)
            return queryset.filter(created__gte=midnight,payment_status__in=status).all()
        else:
            return queryset.all()

# 按下单时间筛选
class Filterbycreated(DoubleTextInputFilter):
    title = u'下单时间'
    parameter_name = ['time','time1']


    def queryset(self, request, queryset):
        if self.value():
            value = self.value()

            try:
                fromtime = time.strptime(value[0], "%Y/%m/%d %H:%M:%S")
                totime = time.strptime(value[1], "%Y/%m/%d %H:%M:%S")
            except:
                if value[0] == None and value[1] == None:
                    pass
                else:
                    messages.error(request,u'时间格式不正确')
            else:
                fromtime = int(time.mktime(fromtime))
                totime = int(time.mktime(totime))
                count = queryset.filter(created__gte=fromtime,created__lte=totime).count()
                messages.success(request, u'共 %s 单' % count)
                return queryset.filter(created__gte=fromtime,created__lte=totime)

class OrderAdmin(SearchAdmin):
    def get_actions(self, request):
        # Disable delete
        actions = super(OrderAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    def has_delete_permission(self, request, obj=None):
        return False
    inlines = [OrderPaymentsInline, OrderShipmentsInline, OrderRemarksInline,OrderHistoriesInline]

    # def queryset(self, request, queryset):
    #     return queryset.filter(created__isnull=False)
    ordering = ['-id']
    list_filter = (('payment_status',UnionFieldListFilter), 'shipping_status', 'refund_status',Filterbyday,Filterbycreated)
    # date_hierarchy = 'created'
    save_as = True
    save_on_top = True

    def  get_refund_status(self, obj):
        refund_status = str(obj.refund_status)
        if refund_status == 'None':
            refund_status = 'none'

        output = ''
        output += '<select name="refund_status">'
        output += '<option value="'
        # output += str(obj.refund_status)
        output += refund_status
        output += '">'
        # output += str(obj.refund_status)
        output += refund_status
        output += '</option>'
        output += '<option value="prepare_refund">prepare refund</option>'
        output += '<option value="partial_refund">partial refund</option>'
        output += '<option value="refund">refund</option>'
        output += '</select>'
        return output
    get_refund_status.allow_tags = True
    get_refund_status.short_description = u'修改状态'

    def  get_payment_status(self, obj):
        payment_status = str(obj.payment_status)
        if payment_status == 'None':
            payment_status = 'none'
        output = ''
        output += '<select name="payment_status">'
        output += '<option value="'
        output += payment_status
        output += '">'
        output += payment_status
        output += '</option>'
        output += '<option value="new">new</option>'
        output += '<option value="new_s">new_s</option>'
        output += '<option value="success">success</option>'
        output += '<option value="pending">pending</option>'
        output += '<option value="failed">failed</option>'
        output += '<option value="cancel">cancel</option>'
        output += '<option value="partial_pail">partial pail</option>'
        output += '<option value="repeat_pay">repeat pay</option>'
        output += '<option value="verify_failed">failed(not pass verific ation)</option>'
        output += '<option value="verify_banned">Faild [Banned List]</option>'
        output += '<option value="verify_pass">success(Pay success and pass verific ation)</option>'
        output += '</select>'
        return output
    get_payment_status.allow_tags = True
    get_payment_status.short_description = u'修改状态'

    def refund_message(self, obj):
        output = ''
        output += '<textarea  name="refund_message"></textarea>'
        return output
    refund_message.allow_tags = True
    refund_message.short_description = '备注'

    def payment_message(self, obj):
        output = ''
        output += '<textarea  name="payment_message"></textarea>'
        return output
    payment_message.allow_tags = True
    payment_message.short_description = '备注'

    def save_model(self, request, obj, form, change):
        try:
            super(OrderAdmin, self).save_model(request, obj, form, change)
        except Exception,e:
            print e
        obj.refund_message_save(request)         
        obj.payment_message_save(request)
        # obj.add_product(request)

    def get_customer_fullname(self,obj):
        output = obj.customer_fullname() 
        return output
    get_customer_fullname.allow_tags = True
    get_customer_fullname.short_description = u'姓名'

    def get_customer_id(self,obj):
        output = obj.customer_id
        return output
    get_customer_id.allow_tags = True
    get_customer_id.short_description = u'客户id'

    def get_customer_created(self,obj):
        output = obj.customer_created()  
        return output
    get_customer_created.allow_tags = True
    get_customer_created.short_description = u'注册时间'

    def get_coupon_type(self,obj):
        output = obj.coupon_type()  
        return output
    get_coupon_type.allow_tags = True
    get_coupon_type.short_description = u'折扣类型'

    def export_order(modeladmin, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(['Id','Status','Ordernum','Email','Amount','Currency','Payment_method', 'Order_from',
            'Shipping_country','Created','Shipping_comment'])
        
        for query in queryset:
            writer.writerow([
                str(query.id).encode('utf-8'),
                # str(query.status).encode('utf-8'),
                query.get_status_display().encode('utf-8'),
                str(query.ordernum).encode('utf-8'),
                str(query.email).encode('utf-8'),
                str(query.amount).encode('utf-8'),
                str(query.currency).encode('utf-8'),
                str(query.payment_method).encode('utf-8'),
                str(query.order_from).encode('utf-8'),
                str(query.shipping_country).encode('utf-8'),
                str(query.created).encode('utf-8'),
                str(query.shipping_comment).encode('utf-8'),
                ])
        return response
    export_order.short_description = u'CSV导出订单'

    def export_catalog_order(modeladmin, request, queryset):
        response, writer = write_csv('catalog_orders')
        writer.writerow(['Ordernum','Currency','Amount','Email','Admin','Times','Created','Verify_Date'])

        # queryset = Order.objects.filter(payment_status='verify_pass')
        for query in queryset:
            times = Order.objects.filter(email=query.email).count()
            row = [
                str(query.ordernum),
                str(query.currency),
                str(query.amount),
                str(query.email),
                str(''),  #admin
                str(times),  #times
                str(query.created),
                str(query.verify_date),
            ]
            writer.writerow(row)
        return response
    export_catalog_order.short_description = u'CSV导出分类订单'

    def order_show(self,obj):
        coupon_type = obj.coupon_type()
        is_marked = ''
        if int(obj.is_marked) == 1:
            is_marked =u'YES'
        else:
            is_marked =u'NO'
        
        output = ""
        output += "<table class='table'>"

        output += "<tr><td><strong>订单号:</strong></td><td>"
        output += str(obj.ordernum)
        output += "</td><td><strong>下单日期:</strong></td><td>"
        output += str(obj.created)
        output += "</td><td><strong>最后修改:</strong></td><td>"
        output += str(obj.updated)
        output += "</td></tr>"

        output += "<tr><td><strong>产品总价:</strong></td><td>"
        output += str(obj.amount_products)
        output += "</td><td><strong>使用积分:</strong></td><td>"
        output += str(obj.points)
        output += "</td><td><strong></strong></td><td>"
        output += ""
        output += "</td></tr>"

        output += "<tr><td><strong>合计:</strong></td><td>"
        output += str(obj.amount)
        output += "</td><td><strong>对美元汇率:</strong></td><td>"
        output += str(obj.rate)
        output += "</td><td><strong></strong></td><td>"
        output += ""
        output += "</td></tr>"

        output += "<tr><td><strong>运费险:</strong></td><td>"
        output += str(obj.order_insurance)
        output += "</td><td><strong>付款方式:</strong></td><td>"
        output += str(obj.payment_method)
        output += "</td><td><strong>支付状态:</strong></td><td>"
        output += str(obj.payment_status)
        output += "</td></tr>"

        output += "<tr><td><strong>发货方式:</strong></td><td>"
        output += str(obj.shipping_method)
        output += "</td><td><strong>发货状态:</strong></td><td>"
        output += str(obj.shipping_status)
        output += "</td><td><strong>快递重量:</strong></td><td>"
        output += str(obj.shipping_weight)
        output += "</td></tr>"

        output += "<tr><td><strong>折扣号:</strong></td><td>"
        output += str(obj.coupon_code)
        output += "</td><td><strong>折扣类型:</strong></td><td>"
        output += str(coupon_type)

        output += "</td><td><strong>折扣金额:</strong></td><td>"
        output += str(obj.amount_coupon)
        output += "</td></tr>"

        output += "<tr><td><strong>订单来源:</strong></td><td>"
        output += str(obj.order_from)
        output += "</td><td><strong>购物车促销:</strong></td><td>"
        try:
            promotion = phpserialize.loads(obj.promotions)
        except:
            promotion = ''

        if promotion and promotion['cart']:
            promotion = promotion['cart']
        else:
            promotion = ''
        output += promotion
        output += "</td><td><strong>异常单:</strong></td><td>"
        output += str(is_marked)
        output += "</td></tr>"

        output += "</table>"
        return output
    order_show.allow_tags = True
    order_show.short_description = u'订单信息'

    def customer_show(self,obj):
        mobile_order = ''
        erp_fee_line_id = str(obj.erp_fee_line_id)
        if erp_fee_line_id:
            if erp_fee_line_id == '1':
                mobile_order = u'YES'
            else:
                mobile_order = u'NO'
        else:
            mobile_order = u'NO'

        output = ""
        output += "<table class='table'>"

        output += "<tr><td><strong>Customer:</strong></td><td>"
        output += str(obj.customer.firstname)+str(obj.customer.lastname)
        output += "</td><td><strong>电子邮件:</strong></td><td>"
        output += str(obj.email)
        output += "</td><td><strong>客户ID:</strong></td><td>"
        output += str(obj.customer.id)
        output += "</td></tr>"

        output += "<tr><td><strong>IP地址:</strong></td><td>"
        output += str(obj.ip)
        output += "</td><td><strong>注册时间:</strong></td><td>"
        output += str(obj.customer.created)
        output += "</td><td><strong>手机订单:</strong></td><td>"
        output += str(mobile_order)
        output += "</td></tr>"

        output += "</table>"
        return output
    customer_show.allow_tags = True
    customer_show.short_description = u'客户信息'

    class Media:
        js = (
                # '/static/js/test.js',
                '/static/js/orderitem_add.js',
            )

    def order_item(self,obj):
        order_id = str(obj.id)
        #获取orderitem中产品个数，用于iframe高度设置
        count = OrderItem.objects.filter(order_id=obj.id).count()
        height = int(count) * 120+450
        height = str("height:")+str(height)+str("px;")
        width = "width:100%;"
        style = "'"+width+height+"'"

        output = ""
        output += "<div ><iframe frameBorder='no' scrolling='no' id='iframepage'  src='/orders/orderitem_add/"+order_id+"' style="+style+"></iframe></div>"

        return output
        
    order_item.allow_tags = True
    order_item.short_description = u'产品基本信息及操作'

    fieldsets = (
        # (u'基本信息',{
        #     'fields':(('ordernum', 'created', 'updated',),('amount_products','amount_shipping','amount_point',),('amount','currency','rate'),
        #     ('order_insurance', 'payment_method', 'payment_status',),('shipping_method', 'shipping_status','shipping_weight',),
        #     ('coupon_code','get_coupon_type', 'amount_coupon'),
        #     ('order_from', 'promotions','is_marked')),
        # }),
        (u'基本信息',{
            'fields':('order_show',('amount_shipping','currency',),'customer_show',),
        }),
        # ('客户信息',{
        #     'fields':(('customer', 'email','get_customer_id',),('ip', 'get_customer_created','erp_fee_line_id') ),
        #     # 'classes': ('collapse',),
        # }),
        ('地址信息',{
            'fields':(('shipping_firstname', 'billing_firstname'),('shipping_lastname', 'billing_lastname'),('shipping_address','billing_address'),
            ('shipping_city', 'billing_city'),('shipping_state', 'billing_state'),('shipping_zip', 'billing_zip'),('shipping_country', 'billing_country'),('shipping_phone', 'billing_phone'), ),
            'classes': ('collapse',),
        }),
        ('退款',{
            'fields':('refund_status','get_refund_status','refund_message' ),
            'classes': ('collapse',),
        }),
        ('支付信息',{
            'fields':('payment_status','get_payment_status','payment_message'),
            'classes': ('collapse',),
        }),
        ('产品信息',{
            'fields':('order_item',),
            'classes': ('collapse',),
        }),

    )
    readonly_fields = ('order_show','customer_show','ordernum','created','updated','amount_products','amount_point','amount','rate',
        'order_insurance', 'payment_method', 'payment_status', 'shipping_method', 'shipping_status','shipping_weight',
        'coupon_code','get_coupon_type', 'amount_coupon','order_from', 'promotions','is_marked',
        'get_refund_status','refund_message','get_payment_status','payment_message', 
        'get_customer_fullname','email','get_customer_id','erp_fee_line_id','get_customer_created','refund_status','get_coupon_type',
        'ip','parent','customer','order_item')
    #readonly_fields = ('ordernum','created', 'updated', 'amount_products','amount_point', 'amount','rate','order_insurance','payment_status',)

    search_fields = ['=ordernum', '=email',]
    list_display = ('id', 'ordernum', 'email', 'created', 'verify_date', 'shipping_date', 'payment_status', 'shipping_status', 'refund_status', 'currency', 'amount', 'payment_method', 'deliver_time','lang' )
    
    # list_display_links = None
    #list_editable = ('status', 'cost', 'weight')
    # actions = [export_order,export_catalog_order]

admin.site.register(Order, OrderAdmin)