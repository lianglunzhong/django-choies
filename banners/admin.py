# -*- coding: utf-8 -*- 
from django.contrib import admin
from .models import Banner
from django.contrib.admin import SimpleListFilter
from django.conf import settings


class BannerTypeManagerFilter(SimpleListFilter):
	title = u'类型'
	parameter_name = 'type'

	def lookups(self, request, model_admin):
		type_list = []	
		type_list.append([0,u'首页轮播大banner'])
		# type_list.append([1,'Index'])
		# type_list.append([2,'Side'])
		type_list.append([3,u'手机站首页轮播banner'])
		type_list.append([4,u'首页分类/促销推荐入口banner'])
		# type_list.append([5,'Index1'])
		type_list.append([6,u'导航栏banner'])
		type_list.append([7,u'新品单品推荐banner'])
		# type_list.append([8,'Index8'])
		type_list.append([9,u'单张红人Lookbook展示banner'])
		type_list.append([10,u'网站顶部banner'])
		type_list.append([11,u'产品页右侧小banner'])
		return type_list

	def queryset(self, request, queryset):
		if self.value() == '0':
			return queryset.filter(type='')
		elif self.value() == '1':
			return queryset.filter(type__in=('index', 'buyers_show', 'index1','index2','index3', 'apparel', 'activity', 'product', 'activities', 'freetrial', 'accessory',))
		elif self.value() == '2':
			return queryset.filter(type='side')
		elif self.value() == '3':
			return queryset.filter(type='phone')
		elif self.value() == '4':
 			return queryset.filter(type='phonecatalog')
 		elif self.value() == '5':
 			return queryset.filter(type='index1')
 		elif self.value() == '6':
 			return queryset.filter(type='newindex')
 		elif self.value() == '7':
 			return queryset.filter(type='index6')
 		# elif self.value() == '8':
 		# 	return queryset.filter(type='index8')
 		elif self.value() == '9':
 			return queryset.filter(type='index12')
 		elif self.value() == '10':
 			return queryset.filter(type='top_banner')
 		elif self.value() == '11':
 			return queryset.filter(type='product_site')
		else:
			return queryset.all()


class BannerVisibilityManagerFilter(SimpleListFilter):
	title = u'是否可见'
	parameter_name = 'visibility'

	def lookups(self, request, model_admin):
		index_list = []
		index_list.append([1,u'可见'])
		index_list.append([2,u'不可见'])
		return index_list

	def queryset(self, request, queryset):
		if self.value() == '1':
			return queryset.filter(visibility=1)
		elif self.value() == '2':
			return queryset.filter(visibility=0)
		else:
			return queryset.all()

class BannerLangManagerFilter(SimpleListFilter):
	title = u'语言'
	parameter_name = 'lang'

	def lookups(self, request, model_admin):
		index_list = []
		index_list.append([1,u'英语'])
		index_list.append([2,u'西语'])
		index_list.append([3,u'德语'])
		index_list.append([4,u'法语'])
		return index_list

	def queryset(self, request, queryset):
		if self.value() == '1':
			return queryset.filter(lang='')
		elif self.value() == '2':
			return queryset.filter(lang='es')
		elif self.value() == '3':
			return queryset.filter(lang='de')
		elif self.value() == '4':
			return queryset.filter(lang='fr')
		else:
			return queryset.all()


class BannerAdmin(admin.ModelAdmin):

	def thumb(self, obj):
		image_url = obj.image
		output = ""
		output += "<img src='/site_media/simages/"
		output += str(image_url)
		output += "' height='120px' width='250px'>" 
		return output   
	thumb.allow_tags = True
	thumb.short_description = u"图片预览"

	def save_model(self, request, obj, form, change):
		try:
			super(BannerAdmin, self).save_model(request, obj, form, change)
		except Exception,e:
			print e
		obj.banner_memcache(request)         
		obj.newindex_banner_memcache(request)         
		obj.top_banner_memcache(request)         
		obj.product_side_memcache(request)         
		obj.change_celebrity_imagename(request)         

	save_as = True
	save_on_top = True
	search_fields = ("title",)
	list_filter = (BannerTypeManagerFilter,BannerVisibilityManagerFilter,BannerLangManagerFilter)
	readonly_fields = ['linkarray','map','thumb']
	fields = ['link', ('image','thumb'),'alt', 'title', 'visibility', 'position','lang']
	list_display = ('id', 'link', 'image', 'alt', 'title','type', 'visibility', 'position','lang','thumb')

admin.site.register(Banner, BannerAdmin)


