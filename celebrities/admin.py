# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Celebrits, CelebrityBlogs

class CelebrityBlogsInline(admin.TabularInline):
	
	model = CelebrityBlogs

	fields = ('type', 'url', 'profile',)
	extra = 0
	max_num = 10
	can_delete = True
class CelebritsAdmin(admin.ModelAdmin):

	ordering = ['-id']
	list_filter =  ('sex', 'level', 'is_able')
	search_fields= ('name', 'email')

	inlines = [CelebrityBlogsInline,]
	save_as = True
	save_on_top = True
	readonly_fields = ('customer',)
	list_display = ('id', 'name', 'email', 'country', 'level','admin', 'created', 'remark', 'is_able', 'height', 'weight', 'bust', 'waist', 'hips')

admin.site.register(Celebrits, CelebritsAdmin)