# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.shortcuts import render
from celebrities import views

urlpatterns = [

    url(r'^celebrity_export/$',views.celebrity_export,name='celebrity_export'),

]

