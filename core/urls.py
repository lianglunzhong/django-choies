from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^pla/$', views.pla, name='pla'),
    url(r'^pla/edit/(?P<id>[0-9]+)$', views.pla_edit, name='edit'),
    url(r'^pla/get/(?P<c>[\w-]+)/(?P<id>[0-9]+)$', views.pla_get, name='get'),
    url(r'^pla/create/(?P<feed>[0-9]+)$', views.pla_create, name='create'),
    url(r'^pla/action/$', views.pla_action, name='pla_aciton'),
    url(r'^pla/delete/(?P<id>[0-9]+)$', views.pla_delete, name='delete'),
]