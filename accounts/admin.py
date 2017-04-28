# -*- coding: utf-8 -*-
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from datetime import datetime
import sys, os ,csv
reload(sys)
sys.setdefaultencoding('utf-8')
# Register your models here.
from accounts.models import Address,Customers,Point_Records,Wishlists,Newsletters,Point_Payments
from orders.models import Order
from products.models import Product
import hashlib
from django.contrib import messages
from core.admin import SearchAdmin


class AddressAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['firstname','lastname',]
    readonly_fields = ('user','customer',)
    list_display = ('id', 'user', 'firstname', 'lastname', 'created', 'updated', 'deleted')

admin.site.register(Address, AddressAdmin)

class PointrecordInline(admin.TabularInline):

    model = Point_Records

    fields = ['amount','type', 'status','admin',]
    extra = 0
    max_num = 100
    can_delete = True

class Point_PaymentsInline(admin.TabularInline):

    model = Point_Payments

    fields = ['created','order_num','amount','note']
    readonly_fields = ['created','order_num','amount','note']
    extra = 0
    max_num = 0
    can_delete = False


class AddressInline(admin.TabularInline):

    model = Address

    def address_edit(self,obj):
        address_id = str(obj.id)
        output = ''
        output += '<a target="blank" href="/admin/accounts/address/'+address_id+'/change/">Edit</a>'
        return output
    address_edit.allow_tags = True
    address_edit.short_description = u'Edit'

    fields = ['firstname','lastname','address','city','state','country','zip','phone','address_edit',]
    readonly_fields = ['firstname','lastname','city','state','country','zip','phone','address_edit']
    extra = 0
    max_num = 0
    can_delete = False

class OrderInline(admin.TabularInline):
    model = Order
    def link(self,obj):
        url = obj.id
        output = "<a href='/admin/orders/order/%s/change'>查看</a>" %(url)
        print output
        return output
    link.short_description = u'link'
    link.allow_tags = True
    list_display = ['ordernum','link',]
    fields = ['ordernum','created','currency','amount','shipping_status','cc_issue','link',]
    readonly_fields = ['ordernum','created','currency','amount','shipping_status','cc_issue','link']
    extra = 0
    max_num = 0
    can_delete = False


class CustomersAdmin(SearchAdmin):
    def get_actions(self, request):
        # Disable delete
        actions = super(CustomersAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False
    def export_customer(modeladmin, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="customer.csv"'
        writer = csv.writer(response)
        writer.writerow(['Id','Email','Firstname','Lastname','Birthday','Status','Gender', 'points',
            'Order_total','ip','vip_level',''])
        
        for query in queryset:
            writer.writerow([
                str(query.id).encode('utf-8'),
                str(query.email).encode('utf-8'),
                str(query.firstname).encode('utf-8'),
                str(query.lastname).encode('utf-8'),
                str(query.birthday).encode('utf-8'),
                str(query.status).encode('utf-8'),
                str(query.gender).encode('utf-8'),
                str(query.points).encode('utf-8'),
                str(query.order_total).encode('utf-8'),
                str(query.ip).encode('utf-8'),
                str(query.vip_level).encode('utf-8'),
                ])
        return response
    export_customer.short_description = u'CSV导出客户'

    def update_flag_3(modeladmin, request, queryset):
        for query in queryset:
            if query.flag != 3:
                query.flag = 3
                query.save()

    update_flag_3.short_description = '用户批量加flag=3的标记(顾客标识，批发用户)'
    def reset_password(modeladmin, request, customers):
        for customer in customers:
            Customers.objects.filter(id=customer.id).update(password=hashlib.sha1('123456').hexdigest())
        messages.success(request,u'重置密码成功')
    reset_password.short_description = '重置密码为123456'
    save_as = True
    save_on_top = True
    search_fields = ['=email']
    list_filter = ('is_vip','vip_level','vip_end')
    list_display = ['id','created','firstname', 'lastname' ,'email','flag','birthday','status','gender','country','last_login_time','last_login_ip']
    fieldsets = (
        (u'客户基本信息',{
            'fields':( 'id','created','firstname', 'lastname' ,'email','birthday','status','gender','country','users_admin'),
        }),
        (u'上次登录信息',{
            'fields':('last_login_time','last_login_ip'),
            }),
        )

    inlines = [PointrecordInline,Point_PaymentsInline,AddressInline,OrderInline]
    actions = [update_flag_3,reset_password]
    readonly_fields = ['last_login_ip','last_login_time','id','created',]

admin.site.register(Customers, CustomersAdmin)

# class WishlistsAdmin(admin.ModelAdmin):
#     search_fields = ['product',]
#     list_display = ['name','created']
#     fields = ['product','customer']
#     readonly_fields = ['product','customer']
# admin.site.register(Wishlists, WishlistsAdmin)


class NewslettersAdmin(SearchAdmin):
    search_fields = ['=email',]
    list_display = ['id','email','firstname','lastname','gender','zip','occupation','birthday','country','created']
admin.site.register(Newsletters,NewslettersAdmin)