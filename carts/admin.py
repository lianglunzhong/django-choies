# -*- coding: utf-8 -*-
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
from django.db.models import Count
from .models import CartItem, Shipping ,Cpromotions,Spromotions,Coupons,Promotions,CustomerCoupons
from .forms import CartItemForm,SpromotionsForm,ProductitemForm,CustomerCouponsForm
from django.contrib.admin.widgets import FilteredSelectMultiple
from dal import autocomplete
import phpserialize
from products.models import Set,Category
from accounts.models import Customers
from carts.models import Promotionfilter
from django.db import IntegrityError, transaction
class CartItemAdmin(admin.ModelAdmin):

    form = ProductitemForm

    def customer_email(self,obj):
        email = ''
        if obj.customer:
            email = obj.customer.email
        return email 
    customer_email.allow_tags = True
    customer_email.short_description = u'customer_email'

    save_as = True
    save_on_top = True
    search_fields = ['item__sku','customer__email']
    readonly_fields = ('customer','customer_email')
    list_display = ('id', 'item', 'customer','customer_email', 'qty', 'created')
    #list_filter = ('status', )
admin.site.register(CartItem, CartItemAdmin)


# class ShippingAdmin(admin.ModelAdmin):
#     save_as = True
#     save_on_top = True
#     #search_fields = ['key', 'sku']
#     #readonly_fields = ('variant', 'user')
#     list_display = ('id', 'name', 'label', 'price', 'default')
#     list_filter = ('active', )
# admin.site.register(Shipping, ShippingAdmin)

class CpromotionsAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    
    def restriction(self,obj):
        #restrictions =
        res = ''
        restrict_catalog = ['','','disabled="disabled"']
        restrict_product = ['','','disabled="disabled"']
        if obj.restrictions:
            res = 'checked="checked"'
            restrictions = phpserialize.loads(obj.restrictions)

            if('restrict_catalog' in restrictions.keys()):
                restrict_catalog[0] = 'checked="checked"'
                restrict_catalog[1] = restrictions['restrict_catalog'][0]
                restrict_catalog[2] = ''

            if('restrict_product' in restrictions.keys()):
                restrict_product[0] = 'checked="checked"'
                restrict_product[1] = restrictions['restrict_product'][0]
                restrict_product[2] = ''
        out=""
        out+='<div class="wl-radio">'
        out+='<div class="radio-inline"><input type="checkbox" id="is_restrict" name="is_restrict" value="1" '+res+'/><p class="mr10 control-static">分类/产品限制</p></div>'
        out+= '<div class="radio-inline"><input name="restrictions" value="restrict_catalog" type="radio" id="restriction_catalog" '+restrict_catalog[0]+'/><p class="mr10 control-static">分类限制</p><input class="mr10" name="restrict_catalog" type="text" class="inline numeric" ' + restrict_catalog[2]+' value="'+restrict_catalog[1]+'" /><p class="mr10 control-static"> (分类id(catalog_id),多个用","隔开)</p></div>'
        out += '<div class="radio-inline"><input name="restrictions" value="restrict_product" type="radio" id="restriction_product" '+restrict_product[0]+'/><p class="mr10 control-static">产品限制</p><input class="mr10" name="restrict_product" type="text"  class="inline" ' + restrict_product[2]+'  value="'+restrict_product[1]+'" /> <p class="mr10 control-static">(产品SKU,多个用","隔开) </p></div>'
        out+='</div>'
        return out
    restriction.allow_tags=True
    restriction.short_description=u'分类/产品限制'

    def condition(self,obj):
        conditions = obj.conditions
        check = ['','','']
        con_sum = ''
        con_qty = ''
        if(conditions):
            if conditions =='whatever':
                check[0] = "checked=\"checked\""
            else:
                con = conditions.split(':')
                if con[0] == 'sum':
                    con_sum = con[1]
                    check[1] = 'checked="checked"'
                else:
                    check[2] = 'checked="checked"'
                    if con:
                        con_qty = con[1]
                    else:
                        con_qty = 1


        out=""
        out+="<div class='wl-radio'>"
        out+='<div class=\'radio-inline\'><input type=\'radio\' name=\'conditions\' value=\'whatever\' id=\'condition_whatever\' '+check[0]+'><p class=\'mr10 control-static\'>全场任意</p></div>'
        out+="<div class='radio-inline'><input name='conditions' value='sum' type='radio' id='condition_sum' "+check[1]+"><p class='mr10 control-static'>金额超时</p><input name='sum' type='number' id='sum'  value='"+con_sum+"'></div>"
        out+="<div class='radio-inline'><input name='conditions' value='quantity' type='radio' id='condition_quantity' "+check[2]+" ><p class='mr10 control-static'>数量超过</p><input name='quantity' type='number' value='"+con_qty+"' id='quantity'></div>"
        out+="</div>"
        return out
    condition.allow_tags=True
    condition.short_description=u'促销条件'
    class Media:
        js = (
            '/static/js/cpromotion.js',
        )
    def action(self,obj):
        # restrict_catalog = ''
        # restrict_product = ''
        action_list = ['','','','','']
        action_discount_rate = ['', '','disabled = "disabled"']
        action_discount_reduce = ['', '','disabled = "disabled"']
        action_largess = ['', '','','']
        action_bundle = ['','']
        action_celebrity = ['']
        if obj.actions:
            actions = phpserialize.loads(obj.actions)
            if('action' in actions.keys()):
                action = actions['action']
                if action == 'discount':
                    action_list[0] = 'checked="checked"'
                    if ('details' in actions.keys()):
                        details = actions['details']
                        res = details.split(':')
                        method = res[0]
                        value = res[1]
                        if method == 'rate':
                            action_discount_rate[0] = 'checked="checked"'
                            action_discount_rate[1] = 'value="'+value+'"'
                            action_discount_rate[2] = ''
                        elif method == 'reduce':
                            action_discount_reduce[0] = 'checked="checked"'
                            action_discount_reduce[1] = 'value="' + value + '"'
                            action_discount_reduce[2] = ''
                elif action == 'largess':
                    action_list[1] = 'checked="checked"'
                    if ('details' in actions.keys()):
                        details = actions['details']['largesses'][0]
                        sku = details['SKU'][0]
                        price = details['price']
                        max_quantity = details['max_quantity']
                        sum_qty = actions['details']['max_sum_quantity']
                        action_largess[0] = 'value="'+sum_qty+'"'
                        action_largess[1] = 'value="'+sku+'"'
                        action_largess[2] = 'value="'+price+'"'
                        action_largess[3] = 'value="'+max_quantity+'"'
                elif action == 'freeshipping':
                    action_list[2] = 'checked="checked"'
                elif action == 'secondhalf': 
                    action_list[3] = 'checked="checked"'
                elif action == 'bundle':
                    action_list[4] = 'checked="checked"'
                    if ('bundlenum' in actions.keys()):
                        bundleprice = actions['bundleprice']
                        num = bundleprice.find(':')
                        value = bundleprice[num + 1:]
                        action_bundle[0] = 'value="' + value + '"'

                        bundlenum = actions['bundlenum']
                        num = bundlenum.find(':')
                        value = bundlenum[num + 1:]
                        action_bundle[1] = 'value="' + value + '"'


        # else:
        #     action_list[0] = 'checked="checked"'
        if obj.celebrity_avoid:
            action_celebrity[0] = 'checked="checked"'

        out=""
        out+="<div class='wl-radio'><ul style='padding-left:0px;'>"
        out+="<li class='radio-inline'><input name=\"promotion_method\" value=\"discount\" id=\"pmethod_1\" type=\"radio\" "+action_list[0]+"/><p class='mr10 control-static'>打折</p>"
        out+= "<input type='radio' name='discount_method' id='method_1' value='rate' "+action_discount_rate[0]+" /><p class='mr10 control-static'>原价乘以:</p><input type='number' name='rate' class='numeric' style='margin-right:0px;' "+action_discount_rate[1]+action_discount_rate[2]+"/>"
        out+= "<p class='mr10 control-static'>%</p><input type='radio' name='discount_method' id='method_2' value='reduce' "+action_discount_reduce[0]+"/><p class='mr10 control-static'>原价减去:</p>"
        out+= "<input type='text'name='reduce'  "+action_discount_reduce[1]+action_discount_reduce[2]+"/></li><li class='radio-inline'><input name='promotion_method'value='largess'id='pmethod_2'type='radio' "+action_list[1]+"/>"
        if action_largess[0]:
            out +="<p class='mr10 control-static'>赠品</p><p class='mr10 control-static'>最大总数量:</p><input type='number' name='largess_sum_quantity'id='largess_sum_quantity' "+action_largess[0]+"/>"
        else:
            out += "<p class='mr10 control-static'>赠品</p><p class='mr10 control-static'>最大总数量:</p><input type='number' name='largess_sum_quantity'id='largess_sum_quantity'/>"

        out += "<p class='mr10 control-static'>SKU:</p><input name='larges_SKU'id='largess_SKU_1' " + action_largess[1] + "/><p class='mr10 control-static'>价格:</p>"
        out += "<input type='number' name='largess_price' id='largess_price_1' " + action_largess[2] + "/><p class='mr10 control-static'>最大数量:</p>"
        out += "<input type='number' name='largess_quantity'id='largess_quantity_1' " + action_largess[3] + "/>"
        out+="<a style=\"display:none;\" class='mr10 control-static' href='#'id='add_largess'count='1'>+更多赠品</a></li>"
        out+="<li class='radio-inline'><input name='promotion_method'value='freeshipping' id='pmethod_3' type='radio' "+action_list[2]+"/><p class='mr10 control-static'>免运费</p></li><li class='radio-inline'><input name='promotion_method'value='secondhalf' id='pmethod_4' type='radio'  "+action_list[3]+"/>"
        out+="<p class='mr10 control-static'>第二件半价</p></li><li class='radio-inline'><input name='promotion_method'value='bundle'id='pmethod_5'type='radio'  "+action_list[4]+" /><p class='mr10 control-static'>捆绑销售</p><p class='mr10 control-static'>捆绑销售价格:</p>"
        out+="<input type='number'name='bundleprice'"+action_bundle[0]+"/><p class='mr10 control-static'>捆绑销售件数:</p><input type='number'name='bundlenum'"+action_bundle[1]+"/></li>"
        out+="<li class='radio-inline'><input class='mr10' type='checkbox' id='celebrity_avoid' name='celebrity_avoid' value='1' "+action_celebrity[0]+"><p class=' control-static'>红人过滤</p></li>"
        out+="</ul></div>"

        return out
    action.allow_tags=True
    action.short_description=u'促销方式'

    fields = ( 'name', 'brief','es','de','fr','priority','restriction','condition','action','from_date', 'to_date','admin','is_active')

    def save_model(self,request,obj,form,change):
        try:
            super(CpromotionsAdmin,self).save_model(request,obj,form,change)
        except Exception,e:
            print e
        obj.cpromotions(request)
        obj.admin_save(request)

        con=''
        if con:
            pass
        else:
            return False

    readonly_fields=('restriction','condition','action',)
    list_filter=('name','brief','from_date','to_date','admin')
    list_display=('id','name','brief','from_date','to_date','admin')
admin.site.register(Cpromotions,CpromotionsAdmin)    

class SpromotionsAdmin(admin.ModelAdmin):
    form = SpromotionsForm
    save_as = True
    save_on_top = True
    list_display = ('id', 'product_id', 'price', 'created', 'expired', 'admin')
    fields = ('product','price','type','admin','position','expired')
    # readonly_fields = ('product',)
    list_filter=('type',)
    search_fields = ['product__sku','product__id']
admin.site.register(Spromotions,SpromotionsAdmin)

class CustomerCouponsInline(admin.TabularInline):
    model = CustomerCoupons
    form = CustomerCouponsForm
    fields = ['customer']
    extra = 0


class CouponsAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['code',]
    inlines = [CustomerCouponsInline,]
    list_display = ('id', 'code', 'item_sku', 'limit', 'expired', 'admin','is_mailed')
    readonly_fields = ('used',)
    list_filter=('type','usedfor')
admin.site.register(Coupons,CouponsAdmin)

class PromotionsAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True

    class Media:
        js = (
            '/static/js/promotion.js',
        )
    def option(self,obj):
        action_list = ['', '', '', '', '']
        action_value = ['', '', '', '', '']
        disabled = ["disabled='disabled'", "disabled='disabled'", "disabled='disabled'", "disabled='disabled'"]
        if obj.actions:
            actions = obj.actions
            num = obj.actions.find(':')
            method = obj.actions[0:num]
            value  = obj.actions[num+1:]

            if method:
                if method == 'rate':
                    action_list[0] = 'checked="checked"'
                    disabled[0] = ""
                    action_value[0] = value
                elif method == 'reduce':
                    action_list[1] = 'checked="checked"'
                    disabled[1] = ""
                    action_value[1] = value
                elif method == 'equal':
                    action_list[2] = 'checked="checked"'
                    disabled[2] = ""
                    action_value[2] = value
                elif method == 'points':
                    action_list[3] = 'checked="checked"'
                    disabled[3] = ""
                    action_value[3] = value
        else:
            action_list[0] = ''
        out = ""
        out += "<div class='wl-radio'><ul style='padding-left:0px;'>"
        out += "<li class='radio-inline'>"
        out += "<input type='radio' name='discount_method' id='method_1' value='rate' "+action_list[0]+"/><p class='mr10 control-static'>原价乘以:</p>"
        out += "<input type='number' name='rate' class='numeric' style='margin-right:0px;' "+ disabled[0] +" value='"+action_value[0]+"'/><p class='mr10 control-static'>%</p>"
        out += "<input type='radio' name='discount_method' id='method_2' value='reduce' "+action_list[1]+"/><p class='mr10 control-static'>原价减去:</p>"
        out += "<input type='number'name='reduce' "+ disabled[1] +" value='"+action_value[1]+"'>"
        out += "<input type='radio' name='discount_method' id='method_3' value='equal' "+action_list[2]+"/><p class='mr10 control-static'>原价改至:</p>"
        out += "<input type='number'name='equal' "+ disabled[2] +" value='"+action_value[2]+"'>"
        out += "<input type='radio' name='discount_method' id='method_4' value='points' "+action_list[3]+"/><p class='mr10 control-static'>双倍积分:</p>"
        out += "<input type='number'name='points' "+ disabled[3] +" value='"+action_value[3]+"'>"
        out += "</li></ul></div>"

        return  out
    option.allow_tags = True
    option.short_description = u'促销方式'


    filter_horizontal = ['category','set']
    readonly_fields = ('option',)
    list_display = ('id', 'name', 'brief', 'from_date', 'to_date', 'admin')
    fields = ('name', 'brief', 'args', 'from_date', 'to_date','option','category','set','price_lower','price_upper','is_active', 'is_view', 'order', 'admin', )


    def save_model(self,request,obj,form,change):
        super(PromotionsAdmin,self).save_model(request,obj,form,change)
        obj.promotions(request)
        form.save_m2m()#save manytomany
        obj.promotionfilter()

        # transaction.on_commit(obj.promotions())
        # transaction.on_commit(obj.promotionfilter())
# 三种保存方法
    # def save_formset(self, request, form, formset, change):
    #     print '++++'
    #     formset.save() # this will save the children
    #     form.instance.save()
    #     form.instance.promotionfilter(request)

    # def save_related(self,request, form, formsets, change):
    #     pass

    # from django.db.models.signals import post_save
    # from django.dispatch import receiver
    # @receiver(post_save, sender=Promotions)
    # def action(sender, instance, **kwargs):
    #     instance.promotionfilter()

admin.site.register(Promotions,PromotionsAdmin)
