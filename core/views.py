#-*- coding: utf-8 -*-
from django.shortcuts import render
import os
import csv
import sys
import pprint
import pytz
from dateutil.parser import parse
from django.utils import timezone
from django.http import HttpResponse

import datetime
import gc
import time
import traceback
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from elasticsearch import Elasticsearch
import products
from core.models import Pla
from django.contrib import messages
from django.shortcuts import redirect
#from products.models import Product
from django.conf import settings
from django.contrib.auth.decorators import login_required

def eparse(value, offset=None):
    try:
        if offset:
            value += offset
        t = parse(value)
    except Exception, e:
        t = None
    return t
# Create your views here.

# now time
def nowtime():
    try:
        now = datetime.datetime.now()
        t = now.strftime('%c')
        t = parse(t)
    except Exception, e:
        print e
    return t

def write_csv(filename):
    response = HttpResponse(content_type='text/csv')
    response.write('\xEF\xBB\xBF')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    writer = csv.writer(response)
    # writer = csv.writer(response,delimiter=b";")
    return response, writer


#下面两个方法可用可不用，Django在对时间操作（比较、导出、页面展示等）的时候会自动转换格式

# 将从页面上获取的时间字符串转换为时间戳
def time_stamp(stime):
    try:
        timearray = time.strptime(str(stime), "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(timearray))
    except Exception,e:
        print e
    return timestamp

#将从数据库读取的时间戳转换成可读的字符串形式
def time_str(timestamp):
    try:
        t = int(timestamp)
        t = time.localtime(t)
        t = time.strftime("%Y-%m-%d %H:%M:%S",t)
    except Exception,e:
        print e
    return t

def time_str2(timestamp):
    try:
        t = int(timestamp)
        t = time.localtime(t)
        t = time.strftime("%Y-%m-%d",t)
    except Exception,e:
        print e
    return str(t)

def time_str3(timestamp):
    try:
        t = int(timestamp)
        t = time.localtime(t)
        t = time.strftime("%Y-%m",t)
    except Exception,e:
        print e
    return str(t)

def time_str4(timestamp):
    try:
        t = int(timestamp)
        t = time.localtime(t)
        t = time.strftime("%Y",t)
    except Exception,e:
        print e
    return str(t)

def time_stamp2(stime):
    try:
        timearray = time.strptime(str(stime), "%Y-%m-%d")
        timestamp = int(time.mktime(timearray))
        return timestamp
    except Exception,e:
        print e

def time_stamp3(stime):
    try:
        timearray = time.strptime(str(stime), "%Y-%m")
        timestamp = int(time.mktime(timearray))
        return timestamp
    except Exception,e:
        print e

def time_stamp4(stime):
    try:
        timearray = time.strptime(str(stime), "%Y")
        timestamp = int(time.mktime(timearray))
        return timestamp
    except Exception,e:
        print e

def time_stamp5(stime):
    try:
        print 1111111111
        timearray = time.strptime(str(stime), "%Y-%m:%w")
        print timearray
        timestamp = int(time.mktime(timearray))
        return timestamp
    except Exception,e:
        print e

def time_stamp6(stime):
    try:
        print 1111111111
        timearray = time.strptime(str(stime), "%Y/%m/%d")
        print timearray
        timestamp = int(time.mktime(timearray))
        return timestamp
    except Exception,e:
        print e

def pp(content):
    '''pprint的简单使用
    '''
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(content)

def esupdate(content):
    #es = Elasticsearch()
    es = Elasticsearch(settings.ES_URL)
    #proinfo = Product.objects.filter(id__in=['70092'])
    # proinfo = Product.objects.filter(id='70092').first()
    # proinfo1 = Product.objects.filter(id='70092')

    print type(content)
    proinfo = products.models.Product.objects.filter(id__in=content).all()
    print proinfo
    for i in proinfo:
        res = i.es_index()
        print res

def timetostr(content):
    tt = str(content)
    timeArray = time.strptime(tt, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

@login_required
def pla(request):
    contents = {}
    contents['data'] = Pla.objects.filter(type=0).all()
    contents['feed'] = Pla.objects.filter(type=1).all()
    print '---'
    for content in contents['feed']:
        if content.country == 'US':
            content.urls = settings.BASE_URL+'googleproduct/choies_googleshopping_feed.txt'
        else:
            content.urls = settings.BASE_URL+'googleproduct/choies_googleshopping_feed.' + (content.country).lower() + '.txt'
    for content in contents['data']:
        if content.country == 'US':
            content.urls = settings.BASE_URL+'googleproduct/choies_googleshopping_feed.'+content.feed+'.txt'
        else:
            content.urls = settings.BASE_URL+'googleproduct/choies_googleshopping_feed.' + content.feed+'.'+(content.country).lower() + '.txt'
    return render(request, 'pla_index.html', contents)

@login_required
def pla_edit(request,id):
    content = {}
    content['data'] = Pla.objects.filter(id=id).get()
    data = content['data']
    title = data.title
    titleArr =str(title).split('++++')
    if data.type == 0:
        data.title1 = titleArr[0]
        data.title2 = titleArr[1]
        description = data.description
        descriptionArr = str(description).split('++++')
        data.description1 = descriptionArr[0]
        data.description2 = descriptionArr[1]
    content['select'] = {'country':['US','UK','AU','CA','FR','ES','DE'],'custom_label':[{1:u'颜色'},{2:u'分类'},{3:u'价格范围'},{4:u'爆款'},{5:u'自定义'}]}
    return render(request,'pla_edit.html',content)

@login_required
def pla_get(request,id,c):
    res = Pla.objects.filter(id=id).get()
    country = ''
    if res.type == 0:
        Pla.objects.filter(country=c).update(status=0)
        Pla.objects.filter(id=id).update(status=1)
        country = (res.country).upper()
        return redirect(settings.BASE_URL+'webpowerfor/mihqtgylls/'+country)
    elif res.type == 1:
        country = (res.country).upper()
        return redirect(settings.BASE_URL+'webpower/mihqtgylls/'+country)

@login_required
def pla_create(request,feed):
    content = {}
    if feed == '0':
        content['data'] = 0
    elif feed == '1':
        content['data'] = 1
    return render(request,'pla_create.html',content)

#数据操作
@login_required
def pla_action(request):
    if request.POST.get('type') == 'create':
        data = {}
        if request.POST.get('create') == '0':
            data['country'] = request.POST.get('country')
            data['feed'] = request.POST.get('feed').strip()
            data['uid'] = request.POST.get('uid').strip()
            data['title'] = request.POST.get('title1').strip()+"++++"+request.POST.get('title2').strip()
            data['description'] = request.POST.get('description1').strip()+"++++"+request.POST.get('description2').strip()
            # data['custom_label_0'] = request.POST.get('custom_label_0','')
            # data['custom_label_1'] = request.POST.get('custom_label_1','')
            # data['custom_label_2'] = request.POST.get('custom_label_2','')
            # data['custom_label_3'] = request.POST.get('custom_label_3','')
            # data['custom_label_4'] = request.POST.get('custom_label_4','')
            data['custom_label'] = request.POST.get('custom_label').strip()
            data['promotion'] = request.POST.get('promotion').strip()
            data['lang'] = request.POST.get('lang').strip()
            data['type'] = 0
            data['status'] = 0
            if request.POST.get('title1').strip():
                data['position'] = '1-'
            else:
                data['position'] = '0-'
            if request.POST.get('title2').strip():
                data['position'] += '1='
            else:
                data['position'] += '0='
            if request.POST.get('description1').strip():
                data['position'] += '1-'
            else:
                data['position'] += '0-'
            if request.POST.get('description2').strip():
                data['position'] += '1'
            else:
                data['position'] += '0'

            print data
            res = Pla.objects.get_or_create(country=data['country'],feed=data['feed'],uid=data['uid'],title=data['title'],description=data['description']
                                            ,custom_label=data['custom_label'],
                                            promotion=data['promotion'],lang=data['lang'],type=data['type'],status=data['status'],position=data['position'])

            if res[1]:
                return redirect('pla')
            else:
                messages.error(request, u'该feed已经存在')
                return redirect('pla')
        elif request.POST.get('create') == '1':
            data['country'] = request.POST.get('country')
            data['promotion'] = request.POST.get('promotion')
            data['status'] = 0
            data['type'] = 1
            res = Pla.objects.get_or_create(country=data['country'],promotion=data['promotion'],status=data['status'],type=data['type'])
            if res[1]:
                messages.success(request, u'创建成功')
                return redirect('pla')
            else:
                messages.error(request, u'该feed已经存在')
                return redirect('pla')

    if request.POST.get('type') == 'edit':
        data = {}
        if request.POST.get('edit') == '0':
            data['country'] = request.POST.get('country')
            data['feed'] = request.POST.get('feed').strip()
            data['uid'] = request.POST.get('uid').strip()
            data['title'] = request.POST.get('title1').strip() + "++++" + request.POST.get('title2').strip()
            data['description'] = request.POST.get('description1').strip() + "++++" + request.POST.get('description2').strip()
            # data['custom_label_0'] = request.POST.get('custom_label_0')
            # data['custom_label_1'] = request.POST.get('custom_label_1')
            # data['custom_label_2'] = request.POST.get('custom_label_2')
            # data['custom_label_3'] = request.POST.get('custom_label_3')
            # data['custom_label_4'] = request.POST.get('custom_label_4')
            data['custom_label'] = request.POST.get('custom_label').strip()
            data['promotion'] = request.POST.get('promotion').strip()
            data['lang'] = request.POST.get('lang').strip()
            data['type'] = 0
            if request.POST.get('title1').strip():
                data['position'] = '1-'
            else:
                data['position'] = '0-'
            if request.POST.get('title2').strip():
                data['position'] += '1='
            else:
                data['position'] += '0='
            if request.POST.get('description1').strip():
                data['position'] += '1-'
            else:
                data['position'] += '0-'
            if request.POST.get('description2').strip():
                data['position'] += '1'
            else:
                data['position'] += '0'
            res = Pla.objects.filter(id=request.POST.get('id')).update(country=data['country'], feed=data['feed'], uid=data['uid'],
                                            title=data['title'], description=data['description'],
                                            custom_label=data['custom_label'],
                                            promotion=data['promotion'], lang=data['lang'], type=data['type'],
                                             position=data['position'])
            if res:
                messages.success(request, u'更新成功')
                return redirect('pla')
            else:
                messages.error(request, u'更新失败')
                return redirect('pla')
            return HttpResponse('1111')
        elif request.POST.get('edit') == '1':
            data['country'] = request.POST.get('country')
            data['promotion'] = request.POST.get('promotion')
            data['type'] = 1
            res = Pla.objects.filter(id=request.POST.get('id')).update(country=data['country'], promotion=data['promotion'],type=data['type'])
            if res:
                messages.success(request, u'更新成功')
                return redirect('pla')
            else:
                messages.error(request, u'更新失败')
                return redirect('pla')

@login_required
def pla_delete(request,id):
    Pla.objects.filter(id=id).delete()
    return redirect('pla')