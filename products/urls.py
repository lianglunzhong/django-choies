from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^c/(?P<link>[\w-]+)/(?P<id>[0-9]+)$', views.category, name='category'),
    url(r'^p/(?P<link>[\w-]+)/(?P<id>[0-9]+)$', views.product, name='product'),
    url(r'^handle/$', views.handle, name='product_handle'),
    url(r'^category/$',views.product_cateogry,name='category_product'),
    url(r'^show_hidden_on_out/$',views.show_hidden_on_out, name='show_hidden_on_out'),
    url(r'^search_attributes/$',views.search_attributes, name='search_attributes'),
    url(r'^render_options/$', views.render_options, name='product_render'),
    url(r'^report/$', views.report, name='product_report'),
    url(r'^tag_sku_view/(?P<id>[0-9]+)$',views.tag_sku_view, name='tag_sku_view'),
    url(r'^test/$', views.test, name='product_test'),
    url(r'^ajax_test/$', views.ajax_test, name='ajax_test'),
    url(r'^report_export/$', views.report_export, name='product_report_export'),
    url(r'^phone_product/$', views.phone_product, name='phone_product'),
    url(r'^product_sale/$', views.product_sale, name='product_sale'),
    url(r'^export_sku/$', views.export_sku, name='export_sku'),
    url(r'^sale_price_memcache/$', views.sale_price_memcache, name='sale_price_memcache'),

    #url(r'^c/(?P<link>\w+)/(?P<id>[0-9]+)$', views.collection, name='collection'),
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]

