# -*- coding: utf-8 -*-
from django.contrib import admin

# Register your models here.
from core.models import Country,Sites,Currencies,Mails,Mail_logs,Docs,Docs_es,Mail_types,Trans
from carts.forms import ProductTransForm
from django.contrib.admin.utils import lookup_needs_distinct

class SearchAdmin(admin.ModelAdmin):
    def get_search_results(self, request, queryset, search_term):
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__istartswith" % field_name  # 优化级别1
                # 优化级别2 暂时用不到 使用__istartswith
                # 优化级别3 暂时用不到 使用__iexact  会产生一个id相关的bug, 可调

        use_distinct = False
        search_fields = self.get_search_fields(request)
        search_term = search_term.strip()
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]

            # 优化or语句为多条sql, 获取每个条件的id list
            ids = []
            for orm_lookup in orm_lookups:
                bit_ids = queryset.filter(**{orm_lookup: search_term}).values_list('id', flat=True)
                ids.extend(bit_ids)
            queryset = queryset.filter(id__in=ids)

            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct




class CountryAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['name','isocode','cn_name' ]
    list_display = ('id', 'name', 'cn_name','isocode', 'position', 'created', 'updated', 'deleted')

admin.site.register(Country, CountryAdmin)




class SitesAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['domain','email' ]
    list_display = ('id', 'domain', 'email','per_page')
    fieldsets = (
        ('Site Basic Information',{
            'fields':('domain','email','ssl','per_page','forum_moderators',),
        }),
        ('Site Basic SEO',{
            'fields':('meta_title','meta_keywords','meta_description','robots','stat_code',),
        }),
         ('test',{
            'fields':('currency','cc_secure_code','cc_payment_url','pp_payment_id','pp_tiny_payment_id','pp_payment_url','pp_submit_url','pp_notify_url','pp_return_url','pp_cancel_return_url','pp_logo_url','pp_api_version','pp_api_user','pp_api_pwd','pp_api_signa','pp_ec_notify_url','pp_ec_return_url','pp_sync_url','ticket_center','fb_api_id','lang','fb_api_secret','elastic_host','cc_payment_id','route_type','checkout','ppec','ppjump','globebill'),
        }),
    )

admin.site.register(Sites, SitesAdmin)


class CurrenciesAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['name','code' ]
    list_display = ('id', 'name', 'fname','code','rate')
    # list_display_links = ('rate',)
    # list_editable  = ('rate',)
    def save_model(self,request,obj,form,change):
        super(CurrenciesAdmin, self).save_model(request, obj, form, change)
        obj.delete_currencies_cache()
admin.site.register(Currencies, CurrenciesAdmin)


class Mail_typesAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['name' ]
    list_display = ('id', 'name', 'created','updated','deleted')

admin.site.register(Mail_types, Mail_typesAdmin)


class MailsAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['type','title' ]
    list_display = ('id', 'type', 'title','is_active')

admin.site.register(Mails, MailsAdmin)


class Mail_logsAdmin(admin.ModelAdmin):
    search_fields = ['type','table','table_id']
    list_display = ('id', 'type', 'table','table_id','email','status','send_date')

admin.site.register(Mail_logs, Mail_logsAdmin)


class DocsAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['name','link' ]
    list_display = ('id', 'name', 'link','is_active')

admin.site.register(Docs, DocsAdmin)


class Docs_esAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    search_fields = ['name','link' ]
    list_display = ('id', 'name', 'link','is_active')

admin.site.register(Docs_es, Docs_esAdmin)

class TransAdmin(admin.ModelAdmin):
    form = ProductTransForm
    save_as = True
    save_on_top = True
    search_fields = ['product__sku']
    list_display = ('product','trans_de','trans_es','trans_fr')
admin.site.register(Trans,TransAdmin)






