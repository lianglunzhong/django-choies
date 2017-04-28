from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.index, name='cart-index'),
    url(r'^handle/$', views.handle, name='cart_handle'),
    url(r'^add_spromotion_memcache/$', views.add_spromotion_memcache,name='cart_promition'),
    url(r'^add_spromotion_memcache_data/$', views.add_spromotion_memcache_data,name='cart_promition_data'),
   #url(r'^c/(?P<link>[\w-]+)/(?P<id>[0-9]+)$', views.category, name='category'),
   #url(r'^p/(?P<link>[\w-]+)/(?P<id>[0-9]+)$', views.product, name='product'),
    #url(r'^c/(?P<link>\w+)/(?P<id>[0-9]+)$', views.collection, name='collection'),
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]

