from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^handle/$', views.handle, name='order_handle'),
    url(r'^add/$', views.add, name='order_add'),
    url(r'^report/$', views.report, name='order_report'),
    url(r'^report_export/$', views.report_export, name='order_report_export'),
    # url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^orderitem_add/(?P<id>[0-9]+)$', views.orderitem_add, name='orderitem_add'),
    url(r'^orderitem_add_ajax/$', views.orderitem_add_ajax, name='orderitem_add_ajax'),
    url(r'^order_item_outstock_ajax/$', views.order_item_outstock_ajax, name='order_item_outstock_ajax'),
    #url(r'^c/(?P<link>\w+)/(?P<id>[0-9]+)$', views.collection, name='collection'),
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]

