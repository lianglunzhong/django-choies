# -*- coding: utf-8  -*-
from __future__ import unicode_literals
from django_unixdatetimefield import UnixDateTimeField
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import sys, os 
import uuid
import phpserialize
import memcache
# from django.core.cache import cache


def get_product_image_upload_path(instance, filename):
	ttt = str(instance.id) 
	return '%s/%s' %('simages/'+ttt,filename)

def get_banner_image_upload_path(instance, filename):
	fn, ext = os.path.splitext(filename)
	if not ext:
		ext = '.jpg'
	name = fn+ext
	# fn, ext = os.path.splitext(filename)
	return '%s/%s' %('simages/',name)


class Banner(models.Model):

	VISIBILITY = (
			(1,u"可见"),
			(0,u"不可见"),
		)

	link = models.CharField(max_length=255, default='', verbose_name=u'链接')
	linkarray = models.TextField(default='',blank=True,null=True, verbose_name=u'Linkarray')
	# image = models.ImageField(upload_to=get_product_image_upload_path, verbose_name=u'图片地址')
	image = models.ImageField(upload_to=get_banner_image_upload_path, verbose_name=u'图片地址')
	alt = models.CharField(max_length=255, verbose_name=u'图片文本', help_text=u'图片无法显示时将用该文字代替') 
	title = models.CharField(max_length=255, default='', verbose_name=u'标题')
	type = models.CharField(max_length=50, blank=True, default='', verbose_name=u'类型')
	map = models.TextField(blank=True, verbose_name=u'Map')
	visibility = models.IntegerField(choices=VISIBILITY, default=1, verbose_name=u'是否可见')
	position = models.IntegerField(verbose_name=u'排序', help_text=u'排序:数字越小排在越前')
	lang = models.CharField(max_length=10, default='', blank=True, verbose_name=u'语种')
	# site_id = models.BooleanField(default=True, verbose_name=u'Site_id')
	created = UnixDateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=u"新增时间")
	updated = UnixDateTimeField(auto_now=True,blank=True,null=True, verbose_name=u"修改时间")

	class Meta:
		verbose_name = u"横幅广告"
		verbose_name_plural = u"横幅广告"


	def __unicode__(self):
		return self.title

	def get_image_thumb(self):
        # images = self.productimage_set.order_by('id').filter(deleted=False).first()
		image = self.image
		if image:
			image_url = str(image)
			image_url_array = image_url.split('/')
			if image_url_array:
				url = "http://d1cr7zfsu1b8qs.cloudfront.net/simages/7JDfNXAhsd.jpg"
			else:
				url = "/static/admin/img/100x100.png"
            # url = 'file:///'+str(images.image)
            # if image_url_array[2]:
            #     url = '/static/'+image_url_array[0]+'/'+image_url_array[1]+'/'+image_url_array[2]
            # else:
            #     url = "/static/admin/img/100x100.png"  
		else:
			url = "/static/admin/img/100x100.png"
        # return format_html(u'<img src="%s" />' % (url))
		return url

	"""banner图片保存时去掉simages/,只保留图片名称"""
	def change_celebrity_imagename(self,request):
		banner = Banner.objects.filter(id=self.id).first()
		if banner:
			image_name = banner.image
			if image_name:
				image_name = str(image_name)
				if image_name.find('simages/') != -1:
					index = image_name.find('simages/')+8
					name = image_name[index:]
					query = Banner.objects.filter(id=self.id).update(image=name)

	def banner_memcache(self,request):
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		lang = ''
		if self.lang:
			lang = str(self.lang)
			# cache_banner_key = '3301site_bannerindex_choies'+lang
			cache_banner_key = '3301site_bannerindex_choies'
		else:
			cache_banner_key = '3301site_bannerindex_choies'
		banners = Banner.objects.filter(visibility=1,lang='').order_by('id').order_by('position')
		i = 0
		cache_data = {}
		for banner in banners:
			data = {}
			data['id'] = banner.id
			data['link'] = str(banner.link)
			data['image'] = str(banner.image)
			data['alt'] = str(banner.alt)
			data['title'] = str(banner.title) 
			data['type'] = str(banner.type)
			data['visibility'] = banner.visibility
			data['position'] = banner.position
			data['lang'] = str(banner.lang)
			data['map'] = str(banner.map)
			data['linkarray'] = str(banner.linkarray)
			# data['created'] = banner.created
			# data['updated'] = banner.updated
			cache_data[i] = data
			i += 1
		# print cache_data
		cache_data = phpserialize.dumps(cache_data)
		cache.set(cache_banner_key,cache_data,3600) 

	def newindex_banner_memcache(self,request):
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		lang = ''
		if self.lang:
			lang = str(self.lang)
			cache_key = '1site_newindex_choies'
		else:
			cache_key = '1site_newindex_choies'
		
		cache_data = {}
		i = 0
		banners = Banner.objects.filter(type='newindex',visibility=1,lang='').order_by('position')
		for banner in banners:
			data = {}
			data['id'] = banner.id
			data['link'] = str(banner.link)
			data['image'] = str(banner.image)
			data['alt'] = str(banner.alt)
			data['title'] = str(banner.title) 
			data['type'] = str(banner.type)
			data['visibility'] = banner.visibility
			data['position'] = banner.position
			data['lang'] = str(banner.lang)
			data['map'] = str(banner.map)
			data['linkarray'] = str(banner.linkarray)
			cache_data[i] = data
			i += 1
		cache_data = phpserialize.dumps(cache_data)
		cache.set(cache_key,cache_data,3600)

	def top_banner_memcache(self,request):
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = '1site_top_banner'
		cache_data = {}
		i = 0
		banners = Banner.objects.filter(type='top_banner',visibility=1,lang='').order_by('position')
		for banner in banners:
			data = {}
			data['id'] = banner.id
			data['link'] = str(banner.link)
			data['image'] = str(banner.image)
			data['alt'] = str(banner.alt)
			data['title'] = str(banner.title) 
			data['type'] = str(banner.type)
			data['visibility'] = banner.visibility
			data['position'] = banner.position
			data['lang'] = str(banner.lang)
			data['map'] = str(banner.map)
			data['linkarray'] = str(banner.linkarray)
			cache_data[i] = data
			i += 1
		cache_data = phpserialize.dumps(cache_data)
		cache.set(cache_key,cache_data,3600)

	def product_side_memcache(self,request):
		cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
		cache_key = '1site_productside'
		cache_data = {}
		i = 0
		banners = Banner.objects.filter(type='product_side',visibility=1,lang='').order_by('position')
		for banner in banners:
			data = {}
			data['id'] = banner.id
			data['link'] = str(banner.link)
			data['image'] = str(banner.image)
			data['alt'] = str(banner.alt)
			data['title'] = str(banner.title) 
			data['type'] = str(banner.type)
			data['visibility'] = banner.visibility
			data['position'] = banner.position
			data['lang'] = str(banner.lang)
			data['map'] = str(banner.map)
			data['linkarray'] = str(banner.linkarray)
			cache_data[i] = data
			i += 1
		cache_data = phpserialize.dumps(cache_data)
		cache.set(cache_key,cache_data,3600)