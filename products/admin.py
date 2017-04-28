# -*- coding: utf-8 -*-
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
import sys, os
import StringIO,csv
reload(sys)
sys.setdefaultencoding('utf-8')
from products.models import *
from django.contrib.admin.widgets import FilteredSelectMultiple
from dal import autocomplete
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from core.views import write_csv
from celebrities.models import Celebrits
from carts.forms import ProductAttributeForm,FilterForm,CelebrityImagesForm,CategoryAllForm,ProductCategoryForm
from dal import autocomplete
from django.conf import settings
from products.forms import *
from core.admin import SearchAdmin


class CategoryAdmin(MPTTModelAdmin,SearchAdmin):

    #分类页根据分类名称自动生成url方法
    class Media:
        js = (
                # '/static/js/test.js',
                '/static/js/orderitem_add.js',
            )
    #根据分类链接自动生成推广url方法
    def extension_url(self,obj):
        output = ''
        link = obj.link
        if link:
            output += str(link) + '-c-' + str(obj.id)
        return output
    extension_url.allow_tags = True
    extension_url.short_description = u"推广url"


    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(CategoryAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        try:
            super(CategoryAdmin, self).save_model(request, obj, form, change)
        except Exception,e:
            print e
        obj.change_category_imagename(request)         

    def export_category(modeladmin, request, queryset):
        response, writer = write_csv('category')
        writer.writerow(['Name','Link','On_menu','Parent_Catalog'])

        for query in queryset:
            link = str(query.link)
            id = str(query.id)
            absolute_link = settings.BASE_URL+ link + '-c-' + id

            parent_catalog = ''
            if query.parent_id:
                categorys = Category.objects.filter(id=query.parent_id)
                for category in categorys:
                    parent_catalog += category.name+'; '

            row = [
                str(query.name),
                str(absolute_link),
                str(query.on_menu),
                str(parent_catalog),
            ]
            writer.writerow(row)
        return response
    export_category.short_description = u'分类导出'

    form = CategoryAllForm

    save_as = True
    save_on_top = True
    search_fields = ['name']
    #ordering = ['id']
    filter_horizontal = ['filters',]
    #list_editable = ('cn_name',)
    # list_filter = ('status',)
    # actions = [export_category,]
    readonly_fields = ['extension_url',]
    list_display = ('id','name', 'link', 'parent', 'level' ,'visibility','on_menu', 'is_brand',)

    fieldsets = (
        (u'基本信息',{
            'fields':('name', 'link','extension_url','parent', 'orderby', 'desc', 'visibility', 'on_menu', 'stereotyped', 'template', 'brief', 'description', 'hot_catalog', 'is_brand', 'price_ranges',),
        }),
        ('Site Basic SEO',{
            'fields':('meta_title','meta_keywords','meta_description',),
            'classes': ('collapse',),
        }),
        ('推荐产品',{
            'fields':('recommended_products', 'image_src', 'image_link', 'image_alt', 'image_map','pimage_src','pimage_map'),
            'classes': ('collapse',),
        }),
    )
    #exclude = ['products']
admin.site.register(Category, CategoryAdmin)


# class CollectionAdmin(MPTTModelAdmin):

#     save_as = True
#     save_on_top = True
#     search_fields = ['name']
#     #ordering = ['id']
#     #filter_horizontal = ['attributes',]
#     #list_editable = ('cn_name',)
#     list_display = ('id', 'name', 'parent', 'level',)
#     #exclude = ['products']
# admin.site.register(Collection, CollectionAdmin)

class ProductAttributeInline(admin.TabularInline):

    model = ProductAttribute

    fields = ['name', 'options',]
    extra = 0
    max_num = 3
    can_delete = True
class ProductFilterInline(admin.TabularInline):

    model = ProductFilter
    form = FilterForm

    fields = ['filter', 'product',]
    extra = 0
    can_delete = True
# class VariantInline(admin.TabularInline):

#     model = Variant

#     fields = ['key', 'sku', 'qty', 'image']
#     extra = 0
#     max_num = 0
#     can_delete = False
class CategoryProductInline(admin.TabularInline):
    form = ProductCategoryForm
    model = CategoryProduct

    fields = ['category']
    extra = 0
    can_delete = True
class CategorySortsInline(admin.TabularInline):

    model = CategorySorts

    fields = ['sort', 'attributes',]
    extra = 0
    max_num = 3
    can_delete = True

class CelebrityImagesInline(admin.TabularInline):

    form = CelebrityImagesForm
    model = CelebrityImages
    # filter_horizontal =['product']
    # def formfield_for_foreignkey(self,db_field,request, **kwargs):
    #     if db_field.name == "celebrity":
    #         kwargs["queryset"] = Celebrits.objects.filter(name=request.user)
    #     return super(CelebrityImagesInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def thumb(self, obj):
        image_url = str(obj.image)
        output = ""
        output += "<img src='/site_media/simages/"
        output += image_url
        output += "' height='200px' width='150px'>" 
        return output 
        
    thumb.allow_tags = True
    thumb.short_description = u"图片预览"

    extra = 0
    max_num = 16
    fields = ('thumb', 'image', 'link_sku', 'celebrity','position')
    readonly_fields = ('thumb',)
    can_delete = True

class ProductImageInline(admin.TabularInline):

    model = ProductImage

    def thumb(self, obj):
        image_url = ''
        image = str(obj.image)
        if image:
            image_url = image
        else:
            image_name = str(obj.id)+'.jpg'
            image_url = 'pimages/'+image_name
            
        output = ""
        output += "<img src='/site_media/"
        output += image_url
        output += "' height='200px' width='150px'>" 
        return output   
    thumb.allow_tags = True
    thumb.short_description = u"图片预览"

    # def default_set(self,obj):

    #     output = ''
    #     output += '<input type="radio" name="is_default" value=" '
    #     output += str(obj.id)
    #     output += ' "/>'
    #     return output
    # default_set.allow_tags = True
    # default_set.short_description = u'设置为默认'

    # def img_url(self, obj):
    #     output = ""
    #     if obj.image:
    #         img = str(obj.image)
    #         image_url_array = img.split('/')
    #         output =u'<a href="/media/%s">原图下载</a><br><a href="/media/%s/%s/%s">1000X1000图片下载</a>'% (obj.image, image_url_array[0], 1000 , image_url_array[2])
    #     else:
    #         output =u'<a href="#">无图片</a>'
    #     return output
    # img_url.allow_tags = True
    # img_url.short_description = u"原图下载地址"
    extra = 0
    fields = ('thumb', 'image','position','is_default')
    readonly_fields = ('thumb',)
    can_delete = True

class ProductAdminForm(autocomplete.FutureModelForm):
    #my_field = forms.ModelMultipleChoiceField(queryset=Product.objects.all(), widget=FilteredSelectMultiple("verbose name", is_stacked=False))
    class Meta:
        fields = '__all__'
        model = Product
       #widgets = {
       #    'tags': autocomplete.TaggingSelect2(
       #        'product-tags'
       #    )
       #}

class ProductitemInlin(admin.TabularInline):
    model = Productitem
    fields = ['sku','status','attribute','stock']
    readonly_fields = ['sku','attribute']
    extra = 0
class ProductAdmin(SearchAdmin):

    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(ProductAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        js = (
                # '/static/js/test.js',
                '/static/js/product_stock_limit.js',
            )

    #产品库存状态限制页面展示
    def stock_status(self,obj):
        size_edit = ''
        product_id = obj.id
        productattribute = ProductAttribute.objects.filter(product_id=product_id).first()
        size_list = []
        if productattribute:
            options = productattribute.options
            size_list = options.split(',')
        for size in size_list:
            num = ''
            stocks = Stocks.objects.filter(product_id=product_id,attributes=size).first()
            if stocks:
                if stocks.stocks:
                    num = str(stocks.stocks)
            size_edit += '<strong>'+size+'&nbsp;:</strong>&nbsp;&nbsp;<input type="text" name="stock_'+size.upper()+'" value="'+num+'"><br><br>'

        stock = obj.stock
        che1 = ''
        che2 = ''
        che1_num = ''
        che2_num = ''
        dis = 'display:none;'
        if stock == -99:
            che1 = 'checked="checked"'
            che1_num = str(-99)
        elif stock == -1:
            che2 = 'checked="checked"'
            che2_num = str(-1)
            dis = ''

        output = ''
        output += '<label for="no_limit_stock_yes"><input type="radio" name="no_limit_stock" class="no_limit_stock" id="no_limit_stock_yes" value="1"'+che1+'/>No limit</label>'
        output += '<label><input type="radio" name="no_limit_stock" class="no_limit_stock" value="0"'+che2+'/>Limit</label>'
        output += '<input name="product[stock]" id="stock" class="product_stock short text required" type="hidden" value="'+che1_num+che2_num+'"><br/></br>'
        output += '<div id="product_stock" style="margin-left:12%;'+dis+'">'+size_edit+'</div>'
        return output
    stock_status.allow_tags = True
    stock_status.short_description = u'库存状态'

    # admin中文名展示
    def picker(self, obj):
        output = ''
        if obj.admin:
            if obj.admin.username:
                output += obj.admin.username
        return output

    picker.allow_tags = True
    picker.short_description = u'选款人'

    form = ProductAdminForm

    def save_formset(self, request, form, formset, change):
        formset.save() # this will save the children
        form.instance.save()
        # form.instance.imagesave(request)  
        form.instance.imagesave_new(request)
        form.instance.default_productimage_memcache(request) 
        form.instance.productimage_memcache(request) 
        form.instance.stock_source()
        form.instance.product_status()
        form.instance.memcache_product1()
        # form.instance.product_stock_limit(request)
        # form.instance.category_product_save(request)
        form.instance.change_celebrity_imagename(request)


    def save_model(self,request,obj,form,change):
        super(ProductAdmin,self).save_model(request,obj,form,change)
        # print request.user.username
        # obj.category_product_save(request)
        # obj.product_stock_limit(request)
        # obj.imagesave(request)
        # obj.memcache_product(request)
        # obj.default_productimage_memcache(request)
        # obj.productimage_memcache(request)
        


    inlines = [CategoryProductInline,ProductImageInline, CelebrityImagesInline,ProductFilterInline,ProductitemInlin]
    def export_product(modeladmin, request, queryset):
        response, writer = write_csv("products")
        writer.writerow(['SKU','Title','Category','Created','Dispaly date','URL to product','Price','RMB Cost',
            'Currency','SearchTerms','Status','Description','Brief','Filter Attributes','Source',
            'Factory','Offline_factory','Admin','Attributes'])
        for query in queryset:
            row = [
                str(query.sku),
                str(query.name),
                str(query.category),
                str(query.created),
                str(query.display_date),
                query.get_absolute_url(),
                str(query.price),
                str(query.total_cost),
                str('US'),
                str(query.keywords),
                query.get_status_display(),
                str(query.description),
                str(query.brief),
                str(query.filter_attributes),
                str(query.source),
                str(query.factory),
                str(query.offline_factory),
                str(query.admin),
                str(query.attributes),
            ]
            writer.writerow(row)
        return response
    export_product.short_description = u'CVS产品导出'

    # def save_model(self,request,obj,form,change):
    #     super(ProductAdmin,self).save_model(request,obj,form,change)
    #     obj.imagesave(request)

    # date_hierarchy = 'created'#时区
    ordering = ['-id']
    list_filter = ('status','visibility',)
    # prepopulated_fields =
    #filter_horizontal = ['category',]
    save_as = True
    save_on_top = True
    search_fields = ['=sku', 'name',]
    
    fieldsets = (
        (u'基本信息',{
            'fields':('name', 'link', 'sku', 'visibility', ('presell', 'presell_message',), 'price','total_cost',
                'extra_fee', 'weight', ('factory', 'offline_factory', 'offline_sku',), ('store', 'taobao_url'), 'position','keywords',
                'source', 'picker', 'cn_name',('set','brand')),
        }),
        (u'产品描述',{
            'fields':('brief', 'description',),
            'classes': ('collapse',),
        }),
        # (u'Catalogs',{
        #     'fields':('category',),
        #     'classes': ('collapse',),
        # }),
        (u'SEO',{
            'fields':('meta_title', 'meta_keywords', 'meta_description', ),
            'classes': ('collapse',),
        }),
    )

    list_display = ('id', 'name', 'set', 'sku', 'price', 'created','display_date', 'visibility', 'status', 'picker','admin', 'source',)
    readonly_fields = ('stock_status','sku','factory', 'offline_factory', 'offline_sku','store', 'taobao_url','offline_picker','total_cost','picker')
    # list_display_links = None
    #list_editable = ('status', 'cost', 'weight')
    # actions = [export_product,]

admin.site.register(Product, ProductAdmin)

# class ProductAttributeAdmin(admin.ModelAdmin):

#     form = ProductAttributeForm

#     save_as = True
#     save_on_top = True
#     search_fields = ['parent__id', 'parent__sku']
#     # readonly_fields = ['product',]
#     fields = ['product','name','options',]
#     list_display = ('id', 'name', )
# admin.site.register(ProductAttribute, ProductAttributeAdmin)


class FilterAdmin(admin.ModelAdmin):
    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(FilterAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    save_as = True
    save_on_top = True
    #search_fields = ['key', 'currency']
    list_display = ('id', 'name', 'options', 'required',)
admin.site.register(Filter, FilterAdmin)

# class OldProductAdmin(admin.ModelAdmin):
#     save_as = True
#     save_on_top = True
#     #search_fields = ['key', 'currency']
#     list_display = ('id', 'sku', 'status')
#     list_filter = ('status', )
# admin.site.register(OldProduct, OldProductAdmin)

# class ProductFilterAdmin(admin.ModelAdmin):
#
#     form = ProductFilterForm
#
#     save_as = True
#     save_on_top = True
#     #search_fields = ['key', 'currency']
#     list_display = ('id', 'product', 'filter', 'options')
#     #list_filter = ('status', )
# admin.site.register(ProductFilter, ProductFilterAdmin)

# class VariantAdmin(admin.ModelAdmin):
#     save_as = True
#     save_on_top = True
#     search_fields = ['key', 'sku']
#     #readonly_fields = ('product', 'key')
#     list_display = ('id', 'product', 'sku', 'key', 'deleted')
#     #list_filter = ('status', )
# admin.site.register(Variant, VariantAdmin)

class TagsAdmin(admin.ModelAdmin):

    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(TagsAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False


    def tag_delete_all(modeladmin, request, queryset):
        for query in queryset:
            TagProduct.objects.filter(tag_id=query.id).update(deleted=1)

    tag_delete_all.short_description = '批量清空tag下的产品'

    def tag_sku(self, obj):
        id = str(obj.id)
        output = ''
        output += '<a target="_blank" href="/products/tag_sku_view/'
        output += id
        output += '">查看</a>'
        return output
    tag_sku.allow_tags = True
    tag_sku.short_description = u'查看tag下关联sku'

    save_as = True
    save_on_top = True
    list_display = ('id','name', 'link', 'position','tag_sku')
    fields = ('name', 'link', 'position','deleted')
    readonly_fields = ('tag_sku',)
    # actions = [tag_delete_all]
    #list_filter = ('status', )
admin.site.register(Tags, TagsAdmin)

class BrandsAdmin(admin.ModelAdmin):

    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(BrandsAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    save_as = True
    save_on_top = True
    list_display = ('id','name', 'label', 'brief')
    #list_filter = ('status', )
admin.site.register(Brands, BrandsAdmin)

class SetAdmin(admin.ModelAdmin):

    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(SetAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    save_as = True
    save_on_top = True
    list_display = ('id','name', 'label', 'brief','catemanger')
    #list_filter = ('status', )
admin.site.register(Set, SetAdmin)

class ColorProductAdmin(admin.ModelAdmin):

    # admin-list
    def get_actions(self, request):
        # Disable delete
        actions = super(ColorProductAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    # admin-detail
    def has_delete_permission(self, request, obj=None):
        return False

    search_fields = ['product_id__sku','group']
    list_display = ('id', 'group','product_id')
    readonly_fields = ('group','product')
    fields = ('product','group')
    def __unicode__(self):
        return ''
admin.site.register(ColorProduct, ColorProductAdmin)