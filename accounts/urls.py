from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [

    url(r'^points/$',views.customer_points,name='customer_points'),
    url(r'^report/$',views.customer_report,name='customer_report'),

]

