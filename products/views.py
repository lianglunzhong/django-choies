#-*- coding: utf-8 -*-
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from products.models import Category,Stocks , Product, Set, Variant,Brands,Tags,TagProduct,CategoryProduct, ProductAttribute, Tags, TagProduct,ProductImage,ProductFilter,Filter,Productitem
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from elasticsearch import Elasticsearch
from django.conf import settings
from dal import autocomplete
from django.views.decorators.csrf import csrf_exempt
import pprint
import phpserialize
import csv
import StringIO
import time, datetime
from core.views import eparse,nowtime,write_csv,time_stamp,esupdate,time_str2,time_str3,time_str4,time_stamp2,time_stamp3,time_stamp4,time_str
from django.http import JsonResponse, HttpResponseRedirect,HttpResponse,JsonResponse
from django.contrib.auth.models import User
from orders.models import Order,OrderItem
from carts.models import Spromotions
from django.db.models import Q
from django.db import connection, transaction
import re
import ast
import demjson
import memcache
import sys
from django.contrib.auth.decorators import login_required
# from django.core.cache import cache
import urllib
import urllib2
import json
from lib.es import es_update
from core.models import Country
from django.db.models import Sum

def memcache_product(product_id):
    url = settings.BASE_URL+'api/delete_product_cache'
    # url = 'http://local.oldchoies.com/api/delete_product_cache'
    postData = product_id
    data = json.dumps(postData)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req,urllib.urlencode({'id':data}))

@login_required
def index(request):
    context = {}
    context['categories'] = Category.objects.all()
    # print context
    return render(request, 'index.html', context)

@login_required
def category(request, id, link):
    # print id
    # print link
    context = {}
    category = get_object_or_404(Category, id=id)
    context['category'] = category

    # get page
    p = int(request.GET.get('p','')) if request.GET.get('p','').isdigit() else 1

    category_list = [category.id]

    # get children
    children = category.get_children()

    # get products
    descendants = category.get_descendants(include_self=True)
    descendant_ids = [descendant.id for descendant in descendants]
    # print descendant_ids
    #product_list = Product.objects.filter(category__in = descendant_ids).distinct()
    
    offset = 0
    limit = 50 

    body = {
            "from" : offset,
            "size" : limit,
            "sort" : [{"price" : "asc"}, ],
            "query":{ 
                "filtered": {
                    "query": {"match_all": {}},

                    "filter": {
                        "bool": {
                            "must": [
                                {"terms": { "category_id": descendant_ids }},
                                {"range": { "price": { "lt": 40, "gte": 30 } }},
                            ]
                        }
                    }
                }
            },
            "aggs": {
                "all_category": {
                    "terms": {"field": "category_id"}
                },
            }
        }

    # print body

    es = Elasticsearch()

    res = es.search(index=settings.ES_INDEX, doc_type="product", body=body)
    data = []

    pprint.pprint(res)
    total = res['hits']['total']
    context['total'] = total

    for hit in res['hits']['hits']:
        item = {}
        item['id'] = hit['_id']
        item['name'] = hit['_source']['name']
        item['sku'] = hit['_source']['sku']
        item['price'] = hit['_source']['price']
        item['url'] = hit['_source']['url']
        item['created'] = hit['_source']['created']
        item['category_id'] = hit['_source']['category_id']
       #item['en_name'] = hit['_source']['en_name']
       #item['sku'] = hit['_source']['sku']
       #item['category_id'] = hit['_source']['category_id']
       #item['brand_id'] = hit['_source']['brand_id']
       #item['brand'] = hit['_source']['brand']
       #item['category'] = hit['_source']['category']
       #item['airports'] = hit['_source']['airports']

        #print("%(name)s / %(en_name)s / " % hit["_source"] + hit['_id'])
        # print item
        data.append(item)

    context['products'] = data
    context['category_filters'] = res['aggregations']['all_category']['buckets']
 
   ## set pagination
   #paginator = Paginator(product_list, 20)

   #try:
   #    products = paginator.page(p)
   #except(EmptyPage, InvalidPage):
   #    #products = paginator.page(paginator.num_pages)
   #    products = []



    return render(request, 'category.html', context)

@login_required
def product(request, link, id):
    context = {}

    product = get_object_or_404(Product, id=id)

    variants = Variant.objects.filter(deleted=False).filter(product=product)
    context['product'] = product 
    context['variants'] = variants

    return render(request, 'product.html', context)

@login_required
def search(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def list(request):
    context = {}
    return render(request, 'index.html', context)

@login_required
def handle(request):
    data = {}
    if request.POST.get('type') == 'do_tag':
        tag_id = request.POST.get('tag', '')
        skus = request.POST.get('skus', '').strip().split('\r\n')
        tagsarr = TagProduct.objects.filter(tag_id=tag_id,deleted=0).values_list('product_id')
        skuarr=Product.objects.filter(sku__in=skus,deleted=0).values_list('id')

        print tagsarr,skuarr
        deleteskuarr = [ i for i in tagsarr if i not in skuarr ]  
        insertskuarr = [ i for i in skuarr if i not in tagsarr ]

        print deleteskuarr,insertskuarr
        if deleteskuarr == insertskuarr:
            for i in insertskuarr:
                TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).update(deleted=0)
        else:
            if deleteskuarr:
                for i in deleteskuarr:
                    TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).update(deleted=1)

            if insertskuarr:
                for i in insertskuarr:
                    query_get=TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).first()
                    if query_get:
                        TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).update(deleted=0)
                    else:
                        TagProduct.objects.create(product_id=i[0],tag_id=tag_id)

        messages.success(request, u'批量打标签成功')
        return redirect('product_handle')

    elif request.POST.get('type') == 'do_tag_insert':
        tag_id = request.POST.get('tag', '')
        skus = request.POST.get('skus', '').strip().split('\r\n')
        tagsarr = TagProduct.objects.filter(tag_id=tag_id,deleted=0).values_list('product_id')
        skuarr=Product.objects.filter(sku__in=skus,deleted=0).values_list('id')

        for i in skuarr:
            query_get=TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).first()
            if query_get:
                TagProduct.objects.filter(product_id=i[0],tag_id=tag_id).update(deleted=0)
            else:
                TagProduct.objects.create(product_id=i[0],tag_id=tag_id)


        messages.success(request, u'批量打标签成功')
        return redirect('product_handle')

    #批量导入SKU-TagId关联:
    elif request.POST.get('type') == 'sku_tagid_relate':
        data_error = ''
        if not request.FILES:
            messages.error(request, u'请选择文件后再提交')
            return redirect('product_handle')

        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['file'].read()))
        header = next(reader)
        std_header = [
            "SKU","TagId"
        ]
        field_header = [
            "sku",'tagid'
        ]
        # 由于bom头的问题, 就不比较第一列的header了
        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('product_handle')

        sku_error = []
        tagid_error = []
        #获取csv每一行的值,i为行数，row为每一行的值，去除bom头和第一行的标题，真正的值应该是从第二行开始的
        for i, row in enumerate(reader,2):
            #将上传的每一行的值与改行的标题一一对应，及(sku,sku值)，(tagid,tagid值)
            res = zip(field_header,row)
            #转化为字典res{'sku':'sku值','tagid':'tagid值'}
            res = dict(res)
            #判断输入的sku是否有误
            product = Product.objects.filter(sku=res['sku']).first()
            if not product:
                sku_error.append(res['sku'])
            else:
                #sku产品存在，则清空该产品之前所关联的所有的标签
                tagproducts = TagProduct.objects.filter(product_id=product.id).delete()

                tagid = res['tagid'].strip()
                #判断tagid是否有输入
                if tagid:
                    #将tagid转化为列表
                    tag_list = tagid.split(',')
                    for tag_id in tag_list:
                        #判断tagid是否输入有误
                        tag = Tags.objects.filter(id=tag_id).first()
                        if tag:
                            #tag正确，则关联该sku和tag到对应的关联表
                            tagproducts = TagProduct.objects.create(product_id=product.id,tag_id=tag.id)
                        else:
                           tagid_error.append(tag_id)

        #判断所有的执行过程中是否有输入错误的sku或tagid
        data_error = ''
        if sku_error:
            sku_error = ' / '.join(sku_error)
            data_error += u'下面的sku输入有误，请确认：' + sku_error
        if tagid_error:
            tagid_error = ' / '.join(tagid_error)
            data_error += u'下面的sku输入有误，请确认：' + tagid_error
        if data_error:
            messages.error(request, data_error)
            return redirect('product_handle')
        else:
            messages.success(request, u'批量导入SKU-TagId关联成功')


    #产品 成本/原售价/现售价 导出
    elif request.POST.get('type') == 'export_cost':
        skus = request.POST.get('skus', '').strip().split('\r\n')

        #判断输入的sku是否有错误
        skuarr = []
        skuerror = []
        for sku in skus:
            product = Product.objects.filter(sku=sku)
            if product:
                skuarr.append(sku)
            else:
                skuerror.append(sku)
        if skuerror:
            messages.error(request, u'sku:'+str(skuerror)+u'有误，无此产品，请检查后重新输入。')
        #导出到csv表格中
        # else:
        #     response, writer = write_csv('export_cost') 
        #     writer.writerow(['SKU',u'原售价',u'现售价',u'美金成本',u'RMB成本',u'重量'])

        #     products = Product.objects.filter(sku__in=skuarr)
        #     expired = nowtime()
            
        #     for sku in skuarr:
        #         for product in products:
        #             if sku == product.sku:
        #                 sale_price = product.price
        #                 spromotions = Spromotions.objects.filter(product_id=product.id,expired__gt=expired).first()
        #                 if spromotions:
        #                     sale_price = spromotions.price
        #                 row = [
        #                     str(product.sku),
        #                     str(product.price),
        #                     str(sale_price),
        #                     str(product.cost),
        #                     str(product.total_cost),
        #                     str(product.weight),
        #                 ]
        #                 writer.writerow(row)

        #     return response


        #不导出，仅在页面上展示
        else:
            dataarr= {}
            header = ['SKU',u'原售价',u'现售价',u'美金成本',u'RMB成本',u'重量']

            products = Product.objects.filter(sku__in=skuarr)
            
            dataarr['products'] = products
            #调用接口，获取产品现售价
            sale_prices = {}
            for product in products:
                product_id = product.id
                product_id = demjson.encode(product_id)
                url = settings.BASE_URL+'adminapi/product_sale_price'
                # url = 'http://local.oldchoies.com/adminapi/product_sale_price'
                req = urllib2.Request(url)
                response = urllib2.urlopen(req,urllib.urlencode({'product_id':product_id})).read()
                sale_price = response.strip('[]')
                sale_prices[int(product.id)] = sale_price

            dataarr['title'] = ''
            dataarr['header'] = header
            dataarr['sale_prices'] = sale_prices
            dataarr['skuarr'] = skuarr
            return render(request,'export_cost.html',dataarr)

    #导出产品(All products、显示的产品、上架的产品、显示并上架的产品)
    elif request.POST.get('type') == 'export_products':
        response, writer = write_csv('products')
        writer.writerow(['SKU','Name','Catalog','Created','Display Date','URL to product','Price','RMB Cost','Currency',
            'URL to image','SearchTerms','Status','Category','Sales','Description','Brief','Filter Attributes',
            'Source','Factory','Offline_factory','Admin','Attributes'])
        
        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(request.POST.get('to'), offset=" 00:00:00") or nowtime()
            to_time = time_stamp(to_time)
        except Exception,e:
            messages.error(request, u'请输入正确的时间格式')
            return redirect('product_handle')

        export_type =  int(request.POST.get('export_type'))
        print export_type
        if export_type == 0:
            products = Product.objects.filter(display_date__gte=from_time,display_date__lt=to_time).order_by('id')
        if export_type == 1:
            products = Product.objects.filter(visibility=1,display_date__gte=from_time,display_date__lt=to_time).order_by('id')
        if export_type == 2:
            products = Product.objects.filter(status=1,display_date__gte=from_time,display_date__lt=to_time).order_by('id')
        if export_type == 3:
            products = Product.objects.filter(visibility=1,status=1,display_date__gte=from_time,display_date__lt=to_time).order_by('id')

        orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,payment_status__in=('verify_pass','success'))

        order_id = []
        for order in orders:
            order_id.append(order.id)

        for product in products:
            categroy_product = CategoryProduct.objects.filter(product_id=product.id).first()
            categoryname = ''
            if categroy_product:
                category = Category.objects.filter(id=categroy_product.category_id).first()
                categoryname = category.name
            # orders = Order.objects.filter(created__gte=from_time,created__lt=to_time,payment_status='verify_pass')

            sales = OrderItem.objects.filter(order_id__in=order_id,product_id=product.id).count()

            # attributes = ''
            # if product.attributes:
            #     print product.attributes
            #     attr = phpserialize.loads(product.attributes)

            row = [
                str(product.sku),
                str(product.name),
                str(''), #Catalog
                str(product.created),
                str(product.display_date),
                str(product.get_absolute_url()), #URL to product
                str(product.price),
                str(product.total_cost),
                str('US'),
                str(''), #URL to image
                str(product.keywords),
                str(product.status),
                str(categoryname),
                str(sales),
                str(product.description),
                str(product.brief),
                str(product.filter_attributes),
                str(product.source),
                str(product.factory),
                str(product.offline_factory),
                # str(product.offline_picker),
                str(product.admin),
                str(product.attributes), #需要做反序列化处理
            ]
            writer.writerow(row)
        return response

    #批量输入store，导出sku
    elif request.POST.get('type') == 'export_store_sku':
        response, writer = write_csv("export_store_sku")
        writer.writerow(["sku", "store"])
        t = nowtime()

        stores = request.POST.get('stores','').strip().split('\r\n')

        #判断输入的store是否有错误
        storeright = []
        storeerror = []
        for store in stores:
            product = Product.objects.filter(store=store)
            if product:
                storeright.append(store)
            else:
                storeerror.append(store)
        if storeerror:
            messages.error(request, u'store:'+str(storeerror)+u'有误，请检查后重新输入。')
        else:
            storearr = Product.objects.filter(store__in=storeright,deleted=0).values_list('id')

            for i in storearr:
                queryset = Product.objects.filter(id=i[0])
                for query in queryset:
                    row = [
                        str(query.sku),
                        str(query.store),
                    ]
                    writer.writerow(row)
            return response

    #导出extra_fee为3的产品
    # elif request.POST.get('type') == 'export_extra_fee3_product':
    #     response, writer = write_csv("customers")
    #     writer.writerow(["sku", "keywords",])

    #     queryset = Product.objects.filter(extra_fee=3)
    #     for query in queryset:
    #         row = [
    #             str(query.sku),
    #             str(query.keywords), 
    #         ]
    #         writer.writerow(row)
    #     return response

    #导出预售产品信息
    elif request.POST.get('type') == 'export_product_prell':
        response,writer = write_csv('Products_presell')
        writer.writerow(['SKU',u'预售状态',u'预售到期时间',u'预售文案',])

        products = Product.objects.all()
        for product in products:
            if product.presell:
                row = [
                    str(product.sku),
                    str(u'预售'),
                    str(product.presell),
                    str(product.presell_message),
                ]
                writer.writerow(row)
        return response


    #导出下架并显示的产品
    elif request.POST.get('type') == 'export_product_outstock':
        response,writer = write_csv('Products_outstock')
        writer.writerow(['Created','SKU','Taobao Url'])

        products = Product.objects.filter(status=0,visibility=1).order_by('id')
        for product in products:
            row = [
                str(product.created),
                str(product.sku),
                str(product.taobao_url),
            ]
            writer.writerow(row)
        return response

    #导出限制库存choies未上架尺码的产品
    elif request.POST.get('type') == 'export_product_stock_status':
        response,writer = write_csv('product_stock_status')
        writer.writerow(['sku','attributes','stocks'])

        product_stocks = Stocks.objects.filter(~Q(stocks=0),isdisplay=0).order_by('-id')
        for product_stock in product_stocks:
            product = Product.objects.filter(id=product_stock.product_id).first()
            status = product.status
            stocks = product.stock
            sku = product.sku
            if stocks != -99 and product_stock.stocks > 0:
                row = [
                    str(sku),
                    str(product_stock.attributes),
                    str(product_stock.stocks),
                ]
                writer.writerow(row)
        return response

    #导出产品数据
    elif request.POST.get('type') == 'export_product_sorts':
        #默认不选则时间则导出所有产品
        has_from_time = request.POST.get('from')
        has_to_time = request.POST.get('to')

        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(request.POST.get('to'), offset=" 23:59:59") or nowtime()
            to_time = time_stamp(to_time)
        except Exception, e:
            messages.error(request, u'请输入正确的时间格式')
            return redirect('product_handle')


        response, writer = write_csv('product_sorts')
        writer.writerow(['id','name','sku','set_name','category'])

        #默认不选则时间则导出所有产品
        if has_from_time and has_to_time:
            ft = "p.created >"+str(from_time)+" and p.created<"+str(to_time)
        elif has_from_time:
            ft = "p.created >"+str(from_time)
        elif has_to_time:
            ft = "p.created >0 and p.created<"+str(to_time)
        else:
            ft = "p.created >0"

        sql="SELECT p.id id,p.name name1, p.sku sku,ss.name,GROUP_CONCAT(c2.name) catalog FROM products_product p LEFT JOIN products_set ss on ss.id = p.set_id LEFT JOIN products_categoryproduct cp ON cp.product_id = p.id LEFT JOIN products_category c2 ON cp.category_id = c2.id  where c2.on_menu = 1 and c2.visibility = 1 and "+ft+" group by p.id  order by p.id desc"
        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        for res in results:
            row = [
                str(res[0]),
                str(res[1]),
                str(res[2]),
                str(res[3]),
                str(res[4]),
            ]
            writer.writerow(row)
        return response
        '''
        #默认不选则时间则导出所有产品
        if has_from_time and has_to_time:
            products = Product.objects.filter(created__gte=from_time,created__lt=to_time).order_by('-id')
        elif has_from_time:
            products = Product.objects.filter(created__gte=from_time).order_by('-id')
        elif has_to_time:
            products = Product.objects.filter(created__lt=to_time).order_by('-id')
        else:
            products = Product.objects.all().order_by('-id')

        for product in products:
            #获取分类名称
            categoryname = ''
            categoryproducts = CategoryProduct.objects.filter(product_id=product.id,deleted=0)
            if categoryproducts:
                for categoryproduct in categoryproducts:
                    categorys = Category.objects.filter(id=categoryproduct.category_id,on_menu=1,visibility=1)
                    if categorys:
                        for category in categorys:
                            categoryname += category.name + ";"

            #去掉最后一个‘;’号
            categoryname = categoryname[0:len(categoryname)-1]

            row = [
                str(product.id),
                str(product.name),
                str(product.sku),
                str(product.set.name),
                str(categoryname),
            ]
            writer.writerow(row)
        return response
        '''

    #导出Admin
    elif request.POST.get('type') == 'export_admin_by_sku':
        response, writer = write_csv("prolistinfo")
        writer.writerow(['sku', 'admin'])

        skus = request.POST.get('skus', '').strip().split('\r\n')

        #判断输入的sku是否有错误
        skuarr = []
        skuerror = []
        for sku in skus:
            product = Product.objects.filter(sku=sku)
            if product:
                skuarr.append(sku)
            else:
                skuerror.append(sku)
        if skuerror:
            messages.error(request, u'sku:'+str(skuerror)+u'有误，无此产品，请检查后重新输入。')
        else:
            products = Product.objects.filter(sku__in=skuarr,deleted=0)
            for product in products:
                user = User.objects.filter(id=product.admin_id).first()
                row = [
                    str(product.sku),
                    str(user.username),
                ]
                writer.writerow(row)
            return response

    #产品信息批量导出
    elif request.POST.get('type') == 'export_products_info':
        response ,writer = write_csv('products_info')
        writer.writerow(['Sku','Description','Size','Weight','Price_sample','Price_small','Price_large','Price_max','Detail','Images_Link'])

        skus = request.POST.get('skus', '').strip().split('\r\n')
        
        #判断输入的sku是否有错误
        skuarr = []
        skuerror = []
        for sku in skus:
            product = Product.objects.filter(sku=sku)
            if product:
                skuarr.append(sku)
            else:
                skuerror.append(sku)
        if skuerror:
            messages.error(request, u'sku:'+str(skuerror)+u'有误，无此产品，请检查后重新输入。')
        else:
            products = Product.objects.filter(sku__in=skuarr,deleted=0)
            for product in products:
                productattribute = ProductAttribute.objects.filter(product_id=product.id).first()
                images_link = ''
                images = ProductImage.objects.filter(product_id=product.id)
                for image in images:
                    images_link += image.image

                row = [
                    str(product.sku),
                    str(product.description),
                    str(productattribute.options), #size
                    str(product.weight),
                    str(product.price), #choies网站原价
                    str(''),  #choies网站现价
                    str(product.cost),  #成本
                    str(product.total_cost),  #RMB成本（采购价格）
                    str(product.brief),
                    str(images_link),  #图片链接
                ]
                writer.writerow(row)
            return response

    #导出产品缩略图,线下供货商,线下SKU,库存信息
    elif request.POST.get('type') == 'export_thumb_sku':

        skus = request.POST.get('skus', '').strip().split('\r\n')

        #判断输入的sku是否有错误
        skuarr = []
        skuerror = []
        for sku in skus:
            product = Product.objects.filter(sku=sku)
            if product:
                skuarr.append(sku)
            else:
                skuerror.append(sku)
        print skuarr
        if skuerror:
            messages.error(request, u'sku:'+str(skuerror)+u'有误，无此产品，请检查后重新输入。')
        #导出到csv表格中
        # else:
        #     response, writer = write_csv('product_thumb_sku') 
        #     writer.writerow(['sku','thumb','offline_factory','offline_sku','stock'])
        #     products = Product.objects.filter(sku__in=skuarr,deleted=0)
        #     for product in products:
        #         row = [
        #             str(product.sku),
        #             str(product.get_image_thumb()),#产品缩略图(待修改)
        #             str(product.offline_factory),
        #             str(product.offline_sku),
        #             str(product.stock),  #库存数量？还是库存限制？
        #         ]
        #         writer.writerow(row)
        #     return response

        #不导出，仅在页面上展示
        else:
            dataarr = {}
            hender = ['SKU',u'缩略图',u'线下供货商',u'线下SKU',u' 库存']
            products = Product.objects.filter(sku__in=skuarr).all()

            images = {}
            for product in products:
                print product.id
                print product.sku
                #使用默认图片
                pimage = ProductImage.objects.filter(product_id=product.id,is_default=1).order_by('id').first()
                #默认图片不存在，使用第一张
                if not pimage:
                    pimage = ProductImage.objects.filter(product_id=product.id).order_by('id').first()

                image_url = ''

                if pimage:
                    image = pimage.image
                    if image:
                        image_url = settings.MEDIA_URL + str(image)
                    else:
                        image_url = settings.MEDIA_URL + 'pimages/' + str(pimage.id) + '.jpg'

                images[int(product.id)] = image_url

            dataarr['images'] = images
            dataarr['products'] = products
            dataarr['hender'] = hender
            dataarr['skuarr'] = skuarr
            return render(request,'export_thumb.html',dataarr)

    #导出产品采购信息
    elif request.POST.get('type') == 'export_product_taobao':
        response, writer = write_csv("product_taobao")
        writer.writerow(['SKU','Taobao Url','Factory','Set Name','Cost','Total Cost','Source','Price',
            'Offline Factory','Admin','Offline Picker','Create','Display Date'])

        taobao_type = int(request.POST.get('taobao_type',0))

        if taobao_type == 1:
            sql = "SELECT A.*,B.username AS picker_name FROM(SELECT p.sku, p.taobao_url, p.factory,p.display_date, s.name AS set_name, p.cost, p.total_cost, p.source, p.price, p.offline_factory, p.created, u.username AS u_name, p.offline_picker_id AS u_picker FROM products_product p LEFT JOIN products_set s ON p.set_id=s.id LEFT JOIN auth_user u ON p.admin_id=u.id WHERE p.visibility = 1 AND p.status = 1) A LEFT JOIN auth_user B ON A.u_picker=B.id"
        else:
            sql = "SELECT A.*,B.username AS picker_name FROM(SELECT p.sku, p.taobao_url, p.factory,p.display_date, s.name AS set_name, p.cost, p.total_cost, p.source, p.price, p.offline_factory, p.created, u.username AS u_name, p.offline_picker_id AS u_picker FROM products_product p LEFT JOIN products_set s ON p.set_id=s.id LEFT JOIN auth_user u ON p.admin_id=u.id ) A LEFT JOIN auth_user B ON A.u_picker=B.id"
        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        (u'CJ000KLP', u'http://www.vvic.com/item/1391586', u'', 1474527878L, u'Coats & Jackets', 20.65, 52.0, u'\u91c7\u8d2d', 44.99, u'\u6c99\u6cb3\u65b0\u91d1\u9a6c3\u697cC072B', 1474527878L, u'\u5468\u6653\u51e4', None, None)
        for r in results:
            display_date = int(r[3])
            display_date = time_str2(display_date)
            create = int(r[10])
            create = time_str2(create)
            row = [
                str(r[0]),
                str(r[1]),
                str(r[2]).decode('utf8'),
                str(r[4]).decode('utf8'),
                str(r[5]),
                str(r[6]),
                str(r[7]).decode('utf8'),
                str(r[8]),
                str(r[9]).decode('utf8'),
                str(r[11]).decode('utf8'),
                str(r[13]).decode('utf8'),
                str(create),
                str(display_date),
            ]
            writer.writerow(row)
        return response
        

    elif request.POST.get('type') == 'export_pro_sorts':
        def isset(v): 
            try : 
                type (eval(v)) 
            except : 
                return  0  
            else : 
                return  1  
        fromtime = request.POST.get('from','')
        totime = request.POST.get('to','')
        response, writer = write_csv("export_pro_sorts-from-"+str(fromtime)+"-to-"+str(totime))
        writer.writerow(['SKU','Name','Catalog','Created','Display Date','URL to product','Price','RMB Cost','Currency','URL to image','SearchTerms','Status','Category','Sales','Description','Brief','Filter Attributes','Source','Factory','Offline_factory','Admin','Attributes'])
        try:
            fromtime = eparse(request.POST.get('from'), offset=" 00:00:00")
            totime = eparse(request.POST.get('to'), offset=" 23:59:59") or nowtime()
            fromtime = time_stamp(fromtime)
            totime = time_stamp(totime)
        except Exception, e:
            messages.error(request, u'请输入正确的时间格式')
            return redirect('product_handle')
        
        print('------------')
      
        products = Product.objects.filter(display_date__gte=fromtime).filter(display_date__lte=totime).all().values()
        userarr = User.objects.all().values('id','first_name','last_name')
        users={}
        
        cursor = connection.cursor()
        for user in userarr:
            users.update({user['id']:(user['first_name']+user['last_name'])})
        for product in products:
            query = "SELECT cp.category_id FROM products_categoryproduct cp LEFT JOIN products_category ca ON (cp.category_id = ca.id) WHERE  cp.product_id = "+str(product['id'])+" AND cp.deleted = 0 AND ca.deleted = 0 AND ca.visibility = 1 AND ca.on_menu=1 "
            cursor.execute(query)
            res = cursor.fetchone()
            #print('res:',res)
            if res:
                category = Category.objects.filter(id=res[0]).values('name')
            else:
                category = Set.objects.filter(id=product['set_id']).values('name')
            # category_id = CategoryProduct.objects.filter(product_id=product['id']).values('category_id')
            # category2 =  Category.objects.filter(id=category_id).values('name')
            if product['configs']:
                get_default_image = phpserialize.loads(product['configs'])
                try:
                    get_default_image['default_image']
                except :
                    try:
                        get_default_image['images_order']
                    except:
                        pass
                    else:
                        images = get_default_image['images_order'].split(',')
                        if get_default_image['images_order']:
                            default_image_id = images[0] 
                        else:
                            default_image_id = 0
                else:
                    default_image_id = get_default_image['default_image']
                try:
                    default_image_id
                except:
                    image=[{'id':0,'suffix':'jpg'}]
                else:  
                    image = ProductImage.objects.filter(id=default_image_id).all().values()
                    if image:
                        pass
                    else:
                        image=[{'id':0,'suffix':'jpg'}]
                image_url = "http://d1cr7zfsu1b8qs.cloudfront.net/pimg/270/"+str(image[0]['id'])+'.'+str(image[0]['suffix'])
                
            attributeArr = phpserialize.loads(product['attributes'])
            attributeStr = 'Size:'
            for attribute in attributeArr['Size']:
                attributeStr += str(attributeArr['Size'][attribute]) + ';' 
  
            description = re.sub("<[^>]*?>","",product['description'])
            brief = re.sub("<[^>]*?>","",product['brief'])
            query = "SELECT COUNT(orders_orderitem.id) AS count FROM orders_orderitem LEFT JOIN orders_order ON orders_orderitem.order_id=orders_order.id WHERE orders_order.payment_status='verify_pass' AND orders_orderitem.product_id= "+str(product['id'])
            cursor.execute(query)
            order = cursor.fetchone()
            # created_str=product['created'].strftime("%Y-%m-%d %H:%M:%S")
            # display_date_str=product['display_date'].strftime("%Y-%m-%d %H:%M:%S")
            row = [
                str(product['sku']),
                str(product['name']),
                str(category[0]['name']),
                str(product['created']),
                str(product['display_date']),
                str('http://www.choies.com/'+product['link']+'_p'+str(product['id'])),
                product['price'],
                product['total_cost'],
                str('US'),
                str(image_url),
                product['keywords'],
                product['status'],
                str(category[0]['name']),
                str(order[0]),
                description,
                brief,
                product['filter_attributes'],
                product['source'],
                product['factory'],
                product['offline_factory'],
                product['offline_picker_id'],
                attributeStr,
            ]

            writer.writerow(row)   
        return response
    
    #批量营销分类Position设置
    elif request.POST.get('type') == 'category_position_set':
        #分类id
        category_id = request.POST.get('category_id', '')
        #产品sku及排序
        skus = request.POST.get('skus', '').strip().split('\r\n')

        if category_id and skus[0] != '':
            #保存输入错误的sku
            skuerror = []

            for skup in skus:
                #拆分sku和其排序
                skuarr = skup.strip('').split(',')
                if skuarr and len(skuarr) == 2:
                    sku = skuarr[0]
                    postion = int(skuarr[1])
                    if sku and postion:
                        positiontwo = 10000 - postion
                        #判断sku
                        product = Product.objects.filter(sku=sku).first()
                        if product:
                            #更新产品分类关联表的排序
                            query_update = CategoryProduct.objects.filter(product_id=product.id,category_id=category_id).update(positiontwo=positiontwo)
                        else:
                            skuerror.append(sku)
            if skuerror:
                skuerror = tuple(skuerror)
                messages.error(request, u"sku:"+str(skuerror)+u"有误，请核对。")
                return redirect('product_handle')
            else:
                messages.success(request, u"更新成功。")
                return redirect('product_handle')
        else:
            messages.error(request, u"请按正确的格式输入sku和排序，并选择分类!")
            return redirect('product_handle')

    elif request.POST.get('type') == 'attributes_by_skus':

        skus = request.POST.get('skus', '').strip().split('\r\n')
        datas = {}
        attributes = []
        products = Product.objects.filter(sku__in=skus).values_list('id','sku')
        if products:
            for product in products:
                items = Productitem.objects.filter(product_id=product[0]).values_list('attribute')
                attribute = ''
                for item in items:
                    attribute += str(item[0]) + ' '
                attributes.append({u'sku':unicode(product[1]),u'size': unicode(attribute)})
            datas['attributes'] = attributes
           
            return render(request, 'attribute_by_skus.html', datas)

    elif request.POST.get('type') == 'info_by_skus':
        skus = request.POST.get('skus', '').strip().split('\r\n')
        data = {}

        products = Product.objects.filter(sku__in=skus).values('name','weight','id','sku','brief','price')
        if not products:
            messages.error(request,u'没有找到对应产品')
            return redirect('product_handle')
        for product in products:
            data[product.get('sku')] = product
            attributes = Productitem.objects.filter(product_id=product.get('id')).values_list('attribute',flat=True)

            # attribute
            data[product.get('sku')]['attribute'] = '/'.join(attributes)

            # image
            images = ProductImage.objects.filter(product_id=product.get('id')).values('id','suffix')
            image_urls = []
            if images:
                for image in images:
                    image_urls.append('https://d1cr7zfsu1b8qs.cloudfront.net/pimg/o/' + str(image.get('id')) +'.'+ str(image.get('suffix')))
            data[product.get('sku')]['images'] = image_urls
            # price
            data[product.get('sku')]['price'] = product.get('price')
                # 获取前台打折后价格
            key = 'product_price_for_admin_'+ str(product.get('id'))
            cache = memcache.Client([settings.MEMCACHE_URL], debug=0)
            small_price = cache.get(key)
            if small_price == None:
                messages.error(request, u'无法获取优惠价格')
                return redirect('product_handle')
            data[product.get('sku')]['small_price'] = small_price
            # detail
            detail = ''
            brief = ''
            pf = ProductFilter.objects.filter(product_id=product.get('id')).all()
            if pf:
                for p in pf:
                    filter = Filter.objects.filter(id=p.filter_id).first()
                    detail += '<div class="a-row"><label>'+filter.name+'</label><span class="selection">'+filter.options+'</span></div>'
            if product.get('brief'):
                brief = product.get('brief')
            detail += '<div class="a-row"><label>Size Availables: </label>'+ brief
            detail += '</div><p style="position: absolute; top: -1999px; left: -1988px;" id="stcpDiv">- See more at: https://www.choies.com</p>'
            detail = detail.replace("\r\n", '&nbsp;')
            detail = detail.replace("\r", '&nbsp;')
            detail = detail.replace("\n", '&nbsp;')
            data[product.get('sku')]['detail'] = detail
       # 输出文件
        response, writer = write_csv("products")
        writer.writerow(['SKU', 'Description', 'Weight', 'Price_large/USD','Price_small/USD','Price for You/USD','Size','Detail', 'Images_link'])

        for sku in data:
            pro = data.get(sku)
            row = [
                str(pro.get('sku')),
                str(pro.get('name')),
                str(pro.get('weight')),
                str(pro.get('price')),
                str(pro.get('small_price')),
                str(''),
                str(pro.get('attribute')),
                str(pro.get('detail'))
            ]
            row = row + pro.get('images')
            print row
            writer.writerow(row)
        return response
    data['tag'] = Tags.objects.filter().values('id', 'name')
    category = Category.objects.values_list('id','link')
    cate = []
    for c in category:
        link = c[1]
        if link:
            res = {}
            res['link'] = str(link) + '-c-' + str(c[0])
            res['id'] = str(c[0])
            cate.append(res)
    data['category'] = cate
    return render(request, 'product_handle.html', data)

@login_required
def product_cateogry(request):
    data={}
    skus = []
    n = 0
    sku_notfound = ''
    sku_notrelate = ''
    if request.method == 'POST':
        tag = request.POST.get('tag', '')
        if request.POST.get('type') != 'products' and request.POST.get('type') != 'delete_products':
            if not request.FILES.get('skus'):
                messages.error(request, u'请选择文件后再提交')
                return redirect('category_product')
            reader = csv.reader(StringIO.StringIO(request.FILES['skus'].read()))
            header = next(reader)
            std_header = [
                "SKU",
            ]
            # 由于bom头的问题, 就不比较第一列的header了
            if header[1:] != std_header[1:]:
                messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
                return redirect('product_handle')
            # print '------'
            for i, row in enumerate(reader,2):
                # print i,row
                skus.append(row[0])
        # print skus
        if request.POST.get('type')=='related':
            #skus=request.POST.get('skus','').strip().split('\r\n')

            updatearr = Product.objects.filter(sku__in=skus,deleted=0).values_list('id')
            livearr=CategoryProduct.objects.filter(category_id=tag).values_list('product_id')
            insertarr = [ i for i in updatearr if i not in livearr ]
            #print updatearr
            if updatearr:
                CategoryProduct.objects.filter(category_id=tag).update(deleted=True)
                CategoryProduct.objects.filter(category_id=tag,product_id__in=updatearr).update(deleted=False,position=0,positiontwo=0)
                for insert in insertarr:
                    CategoryProduct.objects.get_or_create(product_id=insert[0],category_id=tag,deleted=0)
                    n = n+1
                #错误sku提示
                len1=len(skus)
                len2=len(updatearr)
                if len1 != len2:
                    for sku in skus:
                        # print sku
                        if Product.objects.filter(sku=sku,deleted=0).first():
                            pass
                        else:
                            sku_notfound += sku + ','
                messages.success(request, u"操作成功,更新 %s 个sku" % n)
                if sku_notfound:
                    messages.error(request, u"无查询结果的sku:%s"% sku_notfound)
            else:
                #sku不能为空信息提示
                messages.error(request, u"请输入正确的sku")
        elif request.POST.get('type')=='category_add':
            #tag=request.POST.get('tag','')
            #tag =1
            #skus=request.POST.get('skus','').strip().split('\r\n')

            allskus = Product.objects.filter(sku__in=skus).values_list('id',flat=True)
            check = CategoryProduct.objects.filter(category_id=tag).values_list('product_id',flat=True)

            for insert in allskus:
                if insert not in check:
                    CategoryProduct.objects.get_or_create(product_id=insert,category_id=tag)
                    n = n + 1
                    es_update(insert)



            #错误sku提示
            len1=len(skus)
            len2=len(allskus)
            if len1 != len2:
                for sku in skus:
                    if Product.objects.filter(sku=sku).first():
                        pass
                    else:
                        sku_notfound += sku +','
            messages.success(request, u"操作成功,更新 %s 个sku" % n)
            if sku_notfound:
                messages.error(request, u"无查询结果的sku:%s"% sku_notfound)
        elif request.POST.get('type')== 'category_top':
            # 按表格sku顺序排序
            updatearr = []
            sku_notfound = []
            for sku in skus:
                res = Product.objects.filter(sku=sku).values_list('id')
                if res:
                    updatearr.append(res[0])
                else:
                    sku_notfound.append(sku)
            # print updatearr
            position = 9999
            zero = 1
            if updatearr:
                for update in updatearr:
                    # 检查产品分类是否关联，如果没有关联，创建关联数据
                    query = CategoryProduct.objects.filter(product_id=update[0],category_id=tag).first()
                    if not query:
                        CategoryProduct.objects.get_or_create(product_id=update[0], category_id=tag)

                    # 先取消该分类的之前置顶，再更新本次的置顶sku
                    if zero:
                        CategoryProduct.objects.filter(category_id=tag).update(position=0)
                        zero = zero - 1

                    CategoryProduct.objects.filter(product_id=update[0], category_id=tag).update(position=position)
                    position = position - 1
                    n = n + 1
                messages.success(request, u"操作成功,更新 %s 个sku" % n)
                if sku_notfound:
                    str = ''
                    for sku in sku_notfound:
                        str += sku + ','
                    messages.error(request,u'sku不存在: ' + str )

        elif request.POST.get('type')=='position_zerro':
            # tag=request.POST.get('tag')
            # #tag=1
            # skus=request.POST.get('skus','').strip().split('\r\n')

            updatearr=Product.objects.filter(sku__in=skus,deleted=0).values_list('id')
            if updatearr:
                for update in updatearr:
                    query=CategoryProduct.objects.filter(product_id=update[0],category_id=tag,deleted=0).first()
                    if query:
                        CategoryProduct.objects.filter(product_id=update[0],category_id=tag,deleted=0).update(position=0,positiontwo=0)
                        n = n+1
                        # messages.success(request, u"操作成功")
                    else:
                        sku=Product.objects.filter(id=update[0],deleted=0).first()
                        sku_notrelate += sku.sku + ','
                        # messages.error(request, u"请先将该产品分类,sku: %s " % sku.sku)

                #错误sku提示
                len1=len(skus)
                len2=len(updatearr)
                if len1 != len2:
                    for sku in skus:
                        # print sku
                        if Product.objects.filter(sku=sku,deleted=0).first():
                            pass
                        else:
                            sku_notfound += sku.sku +','
                            # messages.error(request, u"无查询结果的sku:%s" % sku)
                messages.success(request, u"操作成功,更新 %s 个sku" % n)
                if sku_notfound:
                    messages.error(request, u"无查询结果的sku:%s"% sku_notfound)
                if sku_notrelate:
                    messages.error(request, u"请检查产品分类,sku: %s" % sku_notrelate)
        elif request.POST.get('type')=='postion':
            # tag=request.POST.get('tag')
            # skus=request.POST.get('skus','').strip().split('\r\n')

            updatearr=Product.objects.filter(sku__in=skus,deleted=0).values_list('id')
            if updatearr:

                for update in updatearr:
                    query=CategoryProduct.objects.filter(product_id=update[0],category_id=tag).first()
                    if query:
                        if query.deleted:
                            sku=Product.objects.filter(id=update[0],deleted=0).first()
                            sku_notrelate += sku.sku + ','
                            #messages.error(request, u"请先将该产品分类,sku: %s " % sku.sku)
                        else:
                            if query.category_id:
                                query_category=Category.objects.filter(id=query.category_id).first()
                                if query_category.on_menu:
                                    CategoryProduct.objects.filter(product_id=update[0],category_id=tag,deleted=0).update(positiontwo=9999)
                                    n = n+1
                                    #messages.success(request, u"操作成功")
                                else:
                                    sku=Product.objects.filter(id=update[0],deleted=0).first()
                                    sku_notrelate += sku.sku + ','
                                    #messages.error(request, u"请核对产品分类,sku%s" % sku.sku)
                    else:
                        sku=Product.objects.filter(id=update[0],deleted=0).first()
                        sku_notrelate += sku.sku + ','

                #错误sku提示
                len1=len(skus)
                len2=len(updatearr)
                if len1 != len2:
                    for sku in skus:
                        print sku
                        if Product.objects.filter(sku=sku,deleted=0).first():
                            pass
                        else:
                            sku_notfound += sku.sku + ','
                            # messages.error(request, u"无查询结果的sku:%s" % sku)
                messages.success(request, u"操作成功,更新 %s 个sku" % n)
                if sku_notfound:
                    messages.error(request, u"无查询结果的sku:%s"% sku_notfound)
                if sku_notrelate:
                    messages.error(request, u"请核对产品分类,sku%s" % sku_notrelate)
            else:
                messages.error(request, u"请输入正确的sku")
        elif request.POST.get('type') == 'cate_basic_save':
            category_links = request.POST.get('category_links', '').strip().split('\r\n')
            category_linkarr = Category.objects.filter(category_link__in=category_links,deleted=0).values_list('id')

            if category_linkarr:
                for i in category_linkarr:
                    re = Category.objects.filter(id=i[0]).update(on_menu=1)
                messages.success(request, u'批量修改分类basic属性成功')
            else:
                messages.error(request, u'请输入正确的分类链接')
        elif request.POST.get('type') == 'products':
            datas = []
            products = CategoryProduct.objects.filter(category_id=tag).all()
            for product in products:
                pro = Product.objects.filter(id=product.id).first()
                if pro:
                    datas.append(pro.sku)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="product.csv"'
            writer = csv.writer(response)
            for data in datas:
                row = [str(data)]
                writer.writerow(row)
            return response
        elif request.POST.get('type') == 'delete_products':
            allow = ['jin.shan@wxzeshang.com','wang.yi@wxzeshang.com','	sun.jin@wxzeshang.com']
            if request.user.email in allow:
                CategoryProduct.objects.filter(category_id=tag).delete()
            else:
                messages.error(request,u'当前用户无权进行该操作')

    return redirect('product_handle')

@login_required
def show_hidden_on_out(request):
    data = {}
    skus = []
    if request.method == 'POST':
        if not request.FILES.get('skus'):
            messages.error(request, u'请选择文件后再提交')
            return redirect('category_product')
        reader = csv.reader(StringIO.StringIO(request.FILES['skus'].read()))
        header = next(reader)
        std_header = [
            "SKU",
        ]
        # 由于bom头的问题, 就不比较第一列的header了
        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('product_handle')

        for i, row in enumerate(reader,2):
            skus.append(row[0])

        if request.POST.get('type') == 'products_show':
            # skus = request.POST.get('skus', '').strip().split('\r\n')
            products=Product.objects.filter(sku__in=skus,deleted=0).all()
            if products:
                for product in products:
                    Product.objects.filter(id=product.id).update(visibility=1)
                    memcache_product(product.id)
                messages.success(request, u'批量显示成功')
            else:
                messages.error(request, u'请输入正确的sku')

        elif request.POST.get('type') == 'products_hidden':
            # skus = request.POST.get('skus', '').strip().split('\r\n')
            skuarr = Product.objects.filter(sku__in=skus).values_list('id')

            if skuarr:
                for i in skuarr:
                    if i[0]:
                        Product.objects.filter(id=i[0]).update(visibility=0)
                        memcache_product(i[0])
                messages.success(request, u'批量隐藏成功')
            else:
                messages.error(request, u'请输入正确的sku')

        elif request.POST.get('type') == 'onstock':
            # skus = request.POST.get('skus', '').strip().split('\r\n')
            products = Product.objects.filter(sku__in=skus,deleted=0).all()

            if products:
                for product in products:
                    #获取产品的size属性，attribute字段
                    attributes = product.attributes
                    sizes = ''
                    #反序列化
                    try:
                        attributes = phpserialize.loads(attributes)
                        sizes = attributes['Size']
                        sizes = sizes.values()
                    except Exception as e:
                        messages.error(request,e)

                    if sizes:
                        for size in sizes:
                            #更新产品item表中的，包含该尺寸的产品item为上架状态
                            Productitem.objects.filter(product_id=product.id,attribute=str(size)).update(status=1)
                        memcache_product(product.id)
                messages.success(request, u'批量上架成功')
            else:
                messages.error(request, u'请输入正确的sku')

        elif request.POST.get('type', '') == 'outstock':
            products = Product.objects.filter(sku__in=skus,deleted=0).all()
            if products:
                for product in products:
                    #更新产品item表的下架状态
                    Productitem.objects.filter(product_id=product.id).update(status=0)
                    memcache_product(product.id)
                messages.success(request, u'批量下架成功')
            else:
                messages.error(request, u'请输入正确的sku')

    product = Product.objects.values_list('id','sku')
    data['tag']=product
    return redirect('product_handle')

@login_required
def search_attributes(request):
    date = {}
    product_list = []
    attribute_list = []
    if request.POST.get('type', '') == 'search_attributes':
        skus = request.POST.get('skus', '').strip().split('\r\n')
        skuarr = Product.objects.filter(sku__in=skus).values_list('id')

        if skuarr:
            for i in skuarr:
                product = Product.objects.filter(id=i[0])
                attribute = ProductAttribute.objects.filter(product_id=i[0])
                product_list.append(product)
                attribute_list.append(attribute)
                # sku = Product.objects.filter(id=i[0]).values_list('sku')
                # attribute = ProductAttribute.objects.filter(product_id=i[0]).values_list('name', 'options')
                # attributes = attribute[0][0] + ':' + attribute[0][1]
                # date[sku[0][0]] = attributes
            date['products'] = product_list
            date['attributes'] = attribute_list
        else:
            messages.error(request, u'请输入正确的sku')
        print date
    return render(request, 'search_attributes.html', date)

@login_required
@csrf_exempt
def render_options(request):
    category = Category.objects.filter(level__gt=0).all()
    query_data = {}
    for i in category:
        level = int(i.level)
        if(level in query_data.keys()):
            ids = str(i.id)
            query_data[level].append(ids)
        else:
            query_data[level] = []
            ids = str(i.id)
            query_data[level].append(ids)

    return JsonResponse(query_data)

@login_required
def tag_sku_view(request,id):
    
    date = {}
    product_list = []

    tag = get_object_or_404(Tags,id=id)
    tagproduct = TagProduct.objects.filter(tag=tag,deleted=0).values_list('product_id')
    for i in tagproduct:
        product = Product.objects.filter(id=i[0])
        product_list.append(product)

    date['products'] = product_list
    date['tag'] = tag
    return render(request, 'tag_sku_view.html', date)

@login_required
def report(request):

    data = {}
    data2 = []
    now = time.time()
    nowtime = now - (now % 86400) + time.timezone

    #ajax数据获取及返回
    if request.method == 'POST':
        #产品状态曲线图数据获取
        if request.POST['type'] == 'product_status_report':
            #时间范围获取及格式转换
            from_time = request.POST['from']
            to_time = request.POST['to']
            if from_time:
                from_time = eparse(from_time, offset=" 00:00:00")
                from_time = time_stamp(from_time)
            else:
                from_time = int(nowtime) - 60 * 86400
            if to_time:
                to_time = eparse(to_time, offset=" 23:59:59")
                to_time = time_stamp(to_time)
            else:
                to_time = int(now)
            #日期类型
            product_date = request.POST['date']
            if product_date == 'day':
                date = "(updated,'%Y-%m-%d') AS date, "
                date1 = "(display_date,'%Y-%m-%d') AS date, "
                date2 = "(o.created,'%Y-%m-%d') AS date, "
            if product_date == 'month':
                date = "(updated,'%Y-%m') AS date, "
                date1 = "(display_date,'%Y-%m') AS date, "
                date2 = "(o.created,'%Y-%m') AS date, "
            if product_date == 'year':
                date = "(updated,'%Y') AS date, "
                date1 = "(display_date,'%Y') AS date, "
                date2 = "(o.created,'%Y') AS date, "
            #产品操作状态
            status = request.POST['status']
            #产品销量
            if status == 'saled':
                sql = "SELECT FROM_UNIXTIME"+date2+" sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+"  GROUP BY date"
            #产品上新
            if status == 'onstock':
                sql = "SELECT FROM_UNIXTIME"+date1+" COUNT(id) AS num FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(from_time)+" AND display_date < "+str(to_time)+" GROUP BY date"
            #产品下架
            if status == 'outstock':
                sql = "SELECT FROM_UNIXTIME"+date+" COUNT(id) AS counts FROM products_product WHERE status=0  AND updated >"+str(from_time)+" AND updated < "+str(to_time)+" GROUP BY date"
            #产品隐藏
            if status == 'hidden':
                sql = "SELECT FROM_UNIXTIME"+date+" COUNT(id) AS counts FROM products_product WHERE  visibility=0 AND updated >"+str(from_time)+" AND updated < "+str(to_time)+" GROUP BY date"
            #数据查询
            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            #查询结果处理
            data2 = []
            data3 = []
            for res in results:
                if product_date == 'day':
                    day = (time_stamp2(res[0])+86400)*1000
                if product_date == 'month':
                    day = time_stamp3(res[0])*1000
                if product_date == 'year':
                    day = time_stamp4(res[0])*1000
                num = int(res[1])
                data2.append([day,num])
                data3.append([str(res[0]),num])
            #设置缓存，用于导出
            cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
            cache_key = 'product_status_export'
            cache_data = {}
            export_time = time_str2(from_time)+'---'+time_str2(to_time)
            cache_data['data'] = data3
            cache_data['status'] = status
            cache_data['export_time'] = export_time
            # cache.set(cache_key,cache_data,10*60)
            
            cache.set(cache_key, cache_data, 10*60)

            #把数据结果返回给ajax
            data['data'] = data2
            data = demjson.encode(data)
            return HttpResponse(data, content_type="application/json")

        #上新产品数及其销量对比统计
        if request.POST['type'] == 'onstock_saled':
            #时间范围获取及格式转换
            from_time = request.POST['from_time']
            to_time = request.POST['to_time']
            if from_time:
                from_time = eparse(from_time, offset=" 00:00:00")
                from_time = time_stamp(from_time)
            else:
                from_time = int(nowtime) - 30 * 86400
            if to_time:
                to_time = eparse(to_time, offset=" 23:59:59")
                to_time = time_stamp(to_time)
            else:
                to_time = int(now)

            #当日上新产品
            sql = "SELECT FROM_UNIXTIME(display_date,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(from_time)+" AND display_date <"+str(to_time)+"  GROUP BY days"
            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            onstock = []
            for res in results:
                day = (time_stamp2(res[0])+86400)*1000
                num = int(res[1])
                onstock.append([day,num])

            #当日上新产品销量
            sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days, sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id INNER JOIN products_product p ON i.product_id=p.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+" AND p.display_date >"+str(from_time)+" AND p.display_date <"+str(to_time)+" GROUP BY days"

            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            onstock_sale = []
            for res in results:
                day = (time_stamp2(res[0])+86400)*1000
                num = int(res[1])
                onstock_sale.append([day,num])


            data = {}
            data['onstock'] = onstock
            data['onstock_sale'] = onstock_sale
            data = demjson.encode(data)

            return HttpResponse(data,content_type="application/json")

        #单品销量统计
        if request.POST['type'] == 'sku_saled':
            #时间范围获取及格式转换
            from_time = request.POST['from_time']
            to_time = request.POST['to_time']
            if from_time:
                from_time = eparse(from_time, offset=" 00:00:00")
                from_time = time_stamp(from_time)
            else:
                from_time = int(nowtime) - 30 * 86400
            if to_time:
                to_time = eparse(to_time, offset=" 23:59:59")
                to_time = time_stamp(to_time)
            else:
                to_time = int(now)

            #获取输入的sku并判断
            sku = request.POST['sku']
            if sku:
                product = Product.objects.filter(sku=sku).first()
                #判断输入的sku是否有误
                if product:
                    product_id = str(product.id)
                    # #日期类型判断
                    # product_date = str(request.POST.get('product_date'))
                    # if product_date == 'day':
                    #     date = "(o.created,'%Y-%m-%d') AS date, "
                    # if product_date == 'month':
                    #     date = "(o.created,'%Y-%m') AS date, "
                    # if product_date == 'year':
                    #     date = "(o.created,'%Y') AS date, "

                    sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days, sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE i.product_id="+product_id+" AND o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+" GROUP BY days"

                    cursor = connection.cursor()
                    cursor.execute(sql)
                    results = cursor.fetchall()

                    sku_sale = []
                    cache_sku_sale = []
                    for res in results:
                        day = (time_stamp2(res[0])+86400)*1000
                        num = int(res[1])
                        sku_sale.append([day,num])
                        cache_sku_sale.append([res[0],num])
            #设置缓存，用于导出
            cache_data = {}
            cache_data['data'] = cache_sku_sale
            cache_data['sku'] = sku
            cache_data['from_time'] = time_str2(from_time)
            cache_data['to_time'] = time_str2(to_time)
            cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
            cache_key = 'sku_saled_export'
            cache.set(cache_key,cache_data,10*60)

                    
            data = {}
            data['sku_sale'] = sku_sale
            data = demjson.encode(data)

            return HttpResponse(data,content_type="application/json")
        
        #新品动销报表模块之上架新品数及上架新品在所选时间段内的总销量对比/销售SKU/SKU——TOP10
        if request.POST['type'] == 'newproduct':
            #时间范围获取及格式转换
            from_time = request.POST['from_time']
            to_time = request.POST['to_time']
            if from_time:
                from_time = eparse(from_time, offset=" 00:00:00")
                from_time = time_stamp(from_time)
            else:
                from_time = int(nowtime) - 7 * 86400
            if to_time:
                to_time = eparse(to_time, offset=" 23:59:59")
                to_time = time_stamp(to_time)
            else:
                to_time = int(now)

            
            '''
            #当日上新产品
            sql = "SELECT FROM_UNIXTIME(display_date,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(from_time)+" AND display_date <"+str(to_time)+"  GROUP BY days"
            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            onstock = []
            for res in results:
                day = time_stamp2(res[0])*1000
                num = int(res[1])
                onstock.append([day,num])
            '''

            #上架新品在所选时间段内的总销量
            #该时间段内上新产品id
            product_list = []
            products = Product.objects.filter(status=1,visibility=1,display_date__gte=from_time,display_date__lt=to_time)
            #该时间范围内上新产品总数
            onstock = products.count()
            #获取新品id列表
            for product in products:
                product_list.append(int(product.id))
            product_list = str(tuple(product_list))

            '''
            #该时间段内每天的新品销量
            sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days, sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE i.product_id IN "+product_list+" AND o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+" GROUP BY days"

            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            saled_total = []
            num = 0
            for res in results:
                day = time_stamp2(res[0])*1000
                num += int(res[1])
                saled_total.append([day,num])
            '''

            #上架新品在所选时间段内的产生销售的总SKU
            sql = "SELECT p.sku AS pid,sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id INNER JOIN products_product p ON i.product_id=p.id WHERE i.product_id IN "+product_list+" AND o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+" GROUP BY pid"

            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            
            #该时间范围内新品销售总数
            saled = 0
            #销售总sku
            sku = []
            skus = {}
            sku_tops= []
            top10= []
            #销售前十SKU
            sku_top10= []
            for res in results:
                saled += int(res[1])
                sku.append(str(res[0]))
                skus[str(res[0])] = str(res[1])
            #对字典按值排序
            sku_tops = sorted(skus.iteritems(),key=lambda d:d[1],reverse = True)
            #选出top10，也可直接对列表截取前十位
            i = 0
            for j in sku_tops:
                top10.append(j)
                i += 1
                if i == 10:
                    break
            '''
            对选出top10升序排列，便于模板页面表格输出结果也是倒序的,
            可直接使用python自带的列表反转函数或者分片操作 b=list(reversed(a)) or b=a[::-1]
            '''
            j = len(top10)
            while j>0:
                sku_top10.append(top10[(j-1)])
                j -= 1

            #新品动销率 销售sku/上新sku:销售总sku的数量/上新产品的数量
            num1 = len(sku)
            num2 = len(product_list)
            if num2 == 0:
                saled_rate = '该时间范围内无上新产品，请重新选择'
            else:
                saled_rate = float('%0.3f'%(float(num1*100)/float(num2)))
                saled_rate = str(saled_rate)+'%'

            #设置缓存，用于导出
            data1 = {}
            data2 = {}
            data1['sku'] = sku
            data2['sku_top10'] = sku_top10
            cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
            cache_key1 = 'export_sku_total'
            cache_key2 = 'export_sku_top10'
            cache.set(cache_key1,data1,600)
            cache.set(cache_key2,data2,600)



            #数据传递
            data = {}
            # data['data0'] = onstock
            # data['data1'] = saled_total
            # data['data2'] = data2
            data['onstock'] = onstock
            data['saled'] = saled
            data['saled_rate'] = saled_rate
            data['sku'] = sku
            data['sku_top10'] = sku_top10
            data = demjson.encode(data)

            return HttpResponse(data,content_type="application/json")

        #每周销量库存统计表模块
        if request.POST['type'] == 'week_saled_stock':
            #++++缓存获取++++
            cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
            cache_key = 'week_saled_stock'
            cache_content = cache.get(cache_key)
            #判断是否有缓存数据
            if cache_content:
                data = {}
                data['products'] = cache_content['products']
                data = demjson.encode(data)
                return HttpResponse(data,content_type="application/json")
            else:
                #获取当前为星期几            
                weekday = time.strftime("%w",time.localtime())
                #获取前面两周的开始时间和结束时间
                if weekday:
                    if str(weekday) == '1':
                        #上周开始时间和结束时间
                        lastweek_starttime = int(nowtime) - 7*86400
                        lastweek_endtime = int(nowtime) - 1*86400
                        #上上周开始时间和结束时间
                        lwbefore_starttime = int(nowtime) - 14*86400
                        lwbefore_endtime = int(nowtime) - 8*86400
                    if str(weekday) == '2':
                        lastweek_starttime = int(nowtime) - 8*86400
                        lastweek_endtime = int(nowtime) - 2*86400

                        lwbefore_starttime = int(nowtime) - 15*86400
                        lwbefore_endtime = int(nowtime) - 9*86400
                    if str(weekday) == '3':
                        lastweek_starttime = int(nowtime) - 9*86400
                        lastweek_endtime = int(nowtime) - 3*86400

                        lwbefore_starttime = int(nowtime) - 16*86400
                        lwbefore_endtime = int(nowtime) - 10*86400
                    if str(weekday) == '4':
                        lastweek_starttime = int(nowtime) - 10*86400
                        lastweek_endtime = int(nowtime) - 4*86400

                        lwbefore_starttime = int(nowtime) - 17*86400
                        lwbefore_endtime = int(nowtime) - 11*86400
                    if str(weekday) == '5':
                        lastweek_starttime = int(nowtime) - 11*86400
                        lastweek_endtime = int(nowtime) - 5*86400

                        lwbefore_starttime = int(nowtime) - 18*86400
                        lwbefore_endtime = int(nowtime) - 12*86400
                    if str(weekday) == '6':
                        lastweek_starttime = int(nowtime) - 12*86400
                        lastweek_endtime = int(nowtime) - 6*86400

                        lwbefore_starttime = int(nowtime) - 19*86400
                        lwbefore_endtime = int(nowtime) - 13*86400
                    if str(weekday) == '7':
                        lastweek_starttime = int(nowtime) - 13*86400
                        lastweek_endtime = int(nowtime) - 7*86400

                        lwbefore_starttime = int(nowtime) - 20*86400
                        lwbefore_endtime = int(nowtime) - 14*86400

                #当前所有在架产品SKU及其销量，库存
                products = []
                sql = "SELECT p.sku,p.display_date,s.num,p.stock,p.source,p.set_id,p.id FROM products_product p LEFT JOIN (SELECT  i.product_id AS pid,sum(IFNULL(i.quantity,0)) AS num FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(lwbefore_starttime)+" AND o.created <"+str(lastweek_endtime)+" GROUP BY pid)  AS s ON p.id = s.pid WHERE p.`status`=1 AND p.visibility=1"
                cursor = connection.cursor()
                cursor.execute(sql)
                results = cursor.fetchall()
                for res in results:
                    sku = res[0].decode('utf8')
                    # source
                    source = res[4].decode('utf8')
                    #当前库存查询
                    stock_now = ''
                    stock = str(res[3])
                    if stock == '-99':
                        stock_now = 'no_limit'
                    elif stock == '-1':
                        stocks = Stocks.objects.filter(product_id=res[6])
                        i = 0
                        for st in stocks:
                            i += st.stocks
                        stock_now = str(i)
                    else:
                        stock_now = '0'
                    #获取set_catagory name
                    set_name = ''
                    set_id = res[5]
                    if set_id and set_id != 'None':
                        sets = Set.objects.filter(id=set_id).first()
                        if sets:
                            set_name = sets.name
                    #展示时间转换
                    display_date = '0'
                    date = res[1]
                    if date and data != 'None':
                        display_date = time_str2(date)
                    #前两周销量判断
                    number = '0'
                    num = str(res[2])
                    if num == 'None':
                        number = '0'
                    else:
                        number = num
                    products.append([sku,display_date,number,stock_now,source,set_name])
                #测试
                #products = [['SK000KAJ', '2016-09-19', '15', 'no_limit', '', u'Skirts'], ['JP000KAS', '2016-09-19', '0', 'no_limit', '', u'Jumpers & Pullovers'], ['JP000KAR', '2016-09-19', '0', 'no_limit', '', u'Jumpers & Pullovers'], ['SK000KBB', '2016-09-19', '0', 'no_limit', '', u'Skirts'], ['SK000KBA', '2016-09-19', '0', 'no_limit', '', u'Skirts'], ['SK000KB9', '2016-09-19', '0', 'no_limit', '', u'Skirts'], ['JP000KDS', '2016-09-19', '0', 'no_limit', '', u'Jumpers & Pullovers'], ['JP000KDR', '2016-09-19', '0', 'no_limit', '', u'Jumpers & Pullovers']]

                data = {}
                data['products'] = products
                #设置缓存
                cache_data = data
                cache.set(cache_key,cache_data,600)
                data = demjson.encode(data)
                return HttpResponse(data,content_type="application/json")
    
    #设置默认打开页面时的数据
    else:
        #默认时间范围
        from_time = int(nowtime) - 60 * 86400
        to_time = int(now)
        #默认日期选择
        product_date = 'day'
        #当日销量
        sql = "SELECT FROM_UNIXTIME(o.created,'%Y-%m-%d') AS days ,sum(IFNULL(i.quantity,0)) AS count FROM orders_orderitem i INNER JOIN orders_order o ON i.order_id=o.id WHERE o.payment_status IN ('verify_pass','success') AND o.is_active=1 AND o.created >"+str(from_time)+" AND o.created <"+str(to_time)+"  GROUP BY days" 
        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        saled = []
        for result in results:
            day = (time_stamp2(result[0])+86400)*1000
            num = int(result[1])
            saled.append([day,num])
        # #当日上新
        # sql = "SELECT FROM_UNIXTIME(display_date,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(from_time)+"  AND display_date <"+str(to_time)+" GROUP BY days"
        # cursor = connection.cursor()
        # cursor.execute(sql)
        # results = cursor.fetchall()
        # onstock = []
        # for result in results:
        #     day = (time_stamp2(result[0])+86400)*1000
        #     num = int(result[1])
        #     onstock.append([day,num])
        # #当日下架数
        # sql = "SELECT FROM_UNIXTIME(updated,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=0  AND updated >"+str(from_time)+" AND updated <"+str(to_time)+" GROUP BY days"
        # cursor = connection.cursor()
        # cursor.execute(sql)
        # results = cursor.fetchall()
        # outstock = []
        # for result in results:
        #     day = (time_stamp2(result[0])+86400)*1000
        #     num = int(result[1])
        #     outstock.append([day,num])
        # #当日隐藏数
        # sql = "SELECT FROM_UNIXTIME(updated,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE  visibility=0 AND updated >"+str(from_time)+" AND updated <"+str(to_time)+" GROUP BY days"
        # cursor = connection.cursor()
        # cursor.execute(sql)
        # results = cursor.fetchall()
        # hidden = []
        # for result in results:
        #     day = (time_stamp2(result[0])+86400)*1000
        #     num = int(result[1])
        #     hidden.append([day,num])

    data['data'] = demjson.encode(saled)
    data['from_time'] = time_str2(from_time)
    data['to_time'] = time_str2(to_time)

    return render(request, 'product_report.html', data)


'''产品报表页面的导出数据操作'''
@login_required
def report_export(request):
    # from django.core.cache import cache
    #每周销量库存统计表导出
    if request.POST.get('type') == 'week_export':
        response,writer = write_csv('week_export')
        writer.writerow(['当前所有在架产品SKU','显示时间','前两周总销量','当前库存','Source','SetName'])
        #获取缓存，前台页面有数据显示，则后台一定有缓存的数据，所以此处可直接获取缓存数据导出，不用重新查询
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = 'week_saled_stock'
        cache_content = cache.get(cache_key)
        if cache_content:
            products = cache_content['products']
            #反转列表，便于导出结果与页面展示一致
            product = products[::-1]
            for p in product:
                row = [
                    str(p[0]),
                    str(p[1]),
                    str(p[2]),
                    str(p[3]),
                    str(p[4]),
                    str(p[5]),
                ]
                writer.writerow(row)
            return response

    #新品动销报表：销售总SKU导出
    if request.POST.get('type') == 'export_sku_total':
        response,writer = write_csv('export_sku_total')
        writer.writerow(['上新产品销售总SKU',])

        #获取缓存的值
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = 'export_sku_total'
        cache_content = cache.get(cache_key)
        if cache_content:
            sku = cache_content['sku']
            #反转列表，便于导出结果与页面展示一致
            sku_list = sku[::-1]
            for i in sku_list:
                row = [
                    str(i)
                ]
                writer.writerow(row)
        return response

    #新品动销报表：销售top10_SKU导出
    if request.POST.get('type') == 'export_sku_top10':
        response,writer = write_csv('export_sku_top10')
        writer.writerow(['新品销量TOP_10 SKU','数量'])

        #获取缓存的值
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = 'export_sku_top10'
        cache_content = cache.get(cache_key)
        if cache_content:
            sku_top10 = cache_content['sku_top10']
            #反转列表，便于导出结果与页面展示一致
            sku_list = sku_top10[::-1]
            for i in sku_list:
                row = [
                    str(i[0]),
                    str(i[1]),
                ]
                writer.writerow(row)
        return response

    #产品操作状态（销售/上新/下架/隐藏）数导出
    if request.POST.get('type') == 'product_status_export':
        response,writer = write_csv('product_status_export')
        #获取缓存的值
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = 'product_status_export'
        cache_content = cache.get(cache_key)
        if cache_content:
            cache_data = cache_content['data']
            status = cache_content['status']
            export_time = cache_content['export_time']
            #导出表格的标题
            if status == 'saled':
                export_title = '销量'
            if status == 'onstock':
                export_title = '上新'
            if status == 'outstock':
                export_title = '下架'
            if status == 'hidden':
                export_title = '隐藏'
            export_title = export_time+'产品'+export_title+'数量'
            writer.writerow([export_title])
            writer.writerow(['日期','数量'])
            for d in cache_data:
                row = [
                    str(d[0]),
                    str(d[1]),
                ]
                writer.writerow(row)
            return response

    #单品销量统计导出
    if request.POST.get('type') == 'sku_saled_export':
        response,writer = write_csv('sku_saled_export')
        #获取缓存的值
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = 'sku_saled_export'
        cache_content = cache.get(cache_key)
        if cache_content:
            cache_data = cache_content['data']
            sku = cache_content['sku']
            from_time = cache_content['from_time']
            to_time = cache_content['to_time']
            title = str(from_time) + '---' + str(to_time) + ':' + sku + u'每日销量统计'
            print title
            print cache_data
            writer.writerow([title])
            writer.writerow([u'日期',u'销量'])
            for c in cache_data:
                row = [
                    str(c[0]),
                    str(c[1]),
                ]
                writer.writerow(row)
            return response

    data = {}
    return render(request, 'product_report_export.html', data)

@login_required    
def test(request):
    content = ['70091','70090']
    esupdate(content)
    #proinfo = Product.objects.filter(id__in=['70092'])
    # proinfo = Product.objects.filter(id='70092').first()
    # proinfo1 = Product.objects.filter(id='70092')
    #print proinfo[0].id
    #sfor i in proinfo:
        


    #es.indices.create(index='my-product_basic_new_',ignore=400)
    #es.index(index="my-index",doc_type="test-type",id=01,body={"sku":"CFAGX1"})
    # res = es.get(index="product_basic_new_", doc_type="product_", id=70093)
    # print(res)
    #res = es.search(index="product_basic_new_", doc_type="product_",id=70093 , ignore=[400, 404])  #获取所有数据
    #d = ast.literal_eval(c)
    # res = es.search(
    #     index='product_basic_new_',
    #     doc_type='product_',
    #     body={
    #       'query': {
    #         'match': {
    #           'id': '70093'
    #         }
    #       }
    #     }
    # )
    # res = ""
    # res = ast.literal_eval(res) 
    # print res
    # c = ast.literal_eval(res)
    # print(c)
    data = {}
    return render(request, 'product_report.html', data)


@login_required
def ajax_test(request):
    data = {}
    now = time.time()
    nowtime = now - (now % 86400) + time.timezone

    if request.method == 'POST':
        #测试数据获取及返回
        if request.POST['type']== 'form001':
            print "it's a test"                            #用于测试
            name = request.POST['name']           #测试是否能够接收到前端发来的name字段
            password = request.POST['password']     #用途同上

            data = {}
            data['name'] = name
            data['password'] = password
            print data
            data = demjson.encode(data)

            return HttpResponse(data,content_type="application/json")     #最后返会给前端的数据，如果能在前端弹出框中显示我们就成功了
            # return JsonResponse(data) 

        #测试
        if request.POST['type'] == 'onstock_vs_saled':
            print 11111111111111
            from_time = request.POST['from_time']
            to_time = request.POST['to_time']
            print from_time
            print to_time

            if from_time:
                from_time = eparse(from_time, offset=" 00:00:00")
                from_time = time_stamp(from_time)
            else:
                from_time = int(nowtime) - 30 * 86400

            to_time = request.POST.get('to')
            if to_time:
                to_time = eparse(to_time, offset=" 23:59:59")
                to_time = time_stamp(to_time)
            else:
                to_time = int(now)


            sql = "SELECT FROM_UNIXTIME(display_date,'%Y-%m-%d') AS days ,COUNT(id) AS counts FROM products_product WHERE status=1 AND visibility=1 AND display_date >"+str(from_time)+" AND display_date <"+str(to_time)+"  GROUP BY days"
            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            print results
            onstock_json = []
            for res in results:
                day = time_stamp2(res[0])*1000
                num = int(res[1])
                onstock_json.append([day,num])

            data = {}
            data['from_time'] = from_time
            data['to_time'] = to_time
            data['onstock'] = onstock_json
            data = demjson.encode(data)
            print data

            return HttpResponse(data,content_type="application/json")

        if request.POST['type'] == 'newproduct':
            print 'hidden_test'
            data0 = [[1258416000000, 1], [1258502400000, 5], [1258588800000, 6],[1258675200000,4]]
            data1 = [[1258416000000, 3], [1258502400000, 4], [1258588800000, 2],[1258675200000,9]]
            data2 = [[1258416000000, 7], [1258502400000, 8], [1258588800000, 5],[1258675200000,1]]
            data = {}
            data['data0'] = data0
            data['data1'] = data1
            data['data2'] = data2
            data = demjson.encode(data)
            print data
            return HttpResponse(data,content_type="application/json")
        
            



    return render(request,'ajax_test.html',data)


@login_required
def phone_product(request):
    data = {}
    cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
    cache_key = 'indexsku'
    cache_key1 = 'indexsku1'
    cache_content = cache.get(cache_key1)
    if cache_content:
        cache_content = cache_content.values()
    
    data['data'] = cache_content
    #首页手机站底部推荐产品修改
    if request.POST.get('type') == 'phone_product':
        #获取sku
        skus = request.POST.get('skus', '')
        #格式转换
        skuarr = skus.strip().split('\r\n')

        if len(skuarr) == 8:
            #判断输入的sku是否有误
            for sku in skuarr:
                product = Product.objects.filter(visibility=1,sku=sku).first()
                if not product:
                    messages.error(request, u'部分SKU存在问题请检查')
                    return redirect('phone_product')
            
            #SKU全都正确,调用前台接口，设置缓存
            #把列表转为字符串
            skus = ','.join(skuarr)
            skus = demjson.encode(skus)

            #调用接口发送邮件
            url = settings.BASE_URL+'adminapi/phone_product'
            # url = 'http://local.oldchoies.com/adminapi/phone_product'
            req = urllib2.Request(url)
            response = urllib2.urlopen(req,urllib.urlencode({'skus':skus}))

            #本地设置缓存，用于后台查看
            cache_data = {}
            i = 0
            for sku in skuarr:
                cache_data[int(i)] = sku
                i += 1
                
            cache.set(cache_key1,cache_data,30*86400)

            messages.success(request, u'成功修改手机版推荐产品')
            return redirect('phone_product')
        else:
            messages.error(request, u'sku个数错误')
            return redirect('phone_product')

    return render(request, 'phone_product.html', data)


@login_required
def product_sale(request):
    data = {}

    sets = Set.objects.all()
    data['sets'] = sets

    countrys = Country.objects.all()
    data['countrys'] = countrys

    return render(request, 'product_sale.html', data)

@login_required
def export_sku(request):
    #SKU销售情况:按下单时间导出
    if request.POST.get('type') == 'export_skus_sale':

        from_time = request.POST.get('from_time', '')
        to_time = request.POST.get('to_time', '')

        if not from_time or not to_time:
            messages.error(request, u'请选择时间')
            return redirect('product_sale')

        try:
            from_time = eparse(from_time, offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(to_time, offset=" 23:59:59")
            to_time = time_stamp(to_time)
        except Exception as e:
            print e
            messages.error(request, u'请输入正确的时间格式时间')
            return redirect('product_sale')


        sql_time = " AND o.created > "+str(from_time)+" AND o.created < "+str(to_time)


        visibility = request.POST.get('visibility')
        sql_vis = ''
        if int(visibility) == 1:
            sql_vis = "p.visibility = 1"
        elif int(visibility) == 0:
            sql_vis = "p.visibility = 0"
        else:
            sql_vis = "p.visibility in (0, 1)"

        sql = "SELECT p.sku,p.display_date,p.price,oi.price,p.cost,oi.shipping_country,oi.num FROM products_product AS p INNER JOIN (SELECT i.product_id,i.price,o.shipping_country,o.created,SUM(IFNULL(i.quantity,0)) AS num FROM orders_orderitem AS i LEFT JOIN orders_order AS o ON i.order_id = o.id WHERE o.is_active=1 AND o.payment_status IN ('success', 'verify_pass') "+str(sql_time)+"  GROUP BY o.shipping_country, i.product_id,i.price ) AS oi ON p.id = oi.product_id WHERE "+str(sql_vis)

        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        response, writer = write_csv('export_sku_sale') 
        writer.writerow(['SKU',u'上架时间',u'销量',u'销售额',u'原价',u'现价(售出时现价)',u'成本价',u'毛利额',u'毛利率',u'国家'])

        std_field = ['sku','display_date','pprice','price','cost','shipping_country','num']

        for row in results:
            res = zip(std_field,row)
            res = dict(res)

            display_date = ''
            try:
                display_date = time_str2(int(res['display_date']))
            except Exception as e:
                print e
                display_date = ''

            #销售额
            sales_amount = ''
            try:
                sales_amount = int(res['num'])*float(res['price'])
            except Exception as e:
                print e
                sales_amount = ''

            #利润率：（现售价-美金成本）/现售价
            profit_rate = ''
            try:
                profit_rate = (float(res['price']) - float(res['cost']))/float(res['price'])
            except Exception as e:
                print e
                profit_rate = ''

            #利润额：现售价-美金成本
            profit_margin  = '' 
            try:
                profit_margin = (float(res['price']) - float(res['cost']))*int(res['num'])
            except Exception as e:
                print e
                profit_margin = '' 
            
            row = [
                str(res['sku']),
                str(display_date),
                str(res['num']),
                str(sales_amount),   #销售额
                str(res['pprice']), #原价
                str(res['price']),  #售价
                str(res['cost']),   #成本
                str(profit_margin),
                str(profit_rate),
                str(res['shipping_country']),
            ]

            writer.writerow(row)

        return response

    ##SKU销售情况:按输入SKU导出
    elif request.POST.get('type') == 'export_skus_sale_by_skus':
        skus = request.POST.get('skus', '')
        bytime = request.POST.get('bytime')

        if not skus:
            messages.error(request, u'请按要求输入正确的sku')
            return redirect('product_sale')
        else:
            skus = skus.strip().split('\r\n')
            skus = tuple(skus)

            products = Product.objects.filter(sku__in=skus).all()

            product_ids = []
            if not products:
                messages.error(request, u'请按要求输入正确的sku')
                return redirect('product_sale')

            for p in products:
                product_ids.append(int(p.id))

            product_ids.append(0)

            product_ids = tuple(product_ids)

            sql = "SELECT p.sku,p.display_date,p.price,oi.price,p.cost,oi.shipping_country,oi.num FROM products_product AS p LEFT JOIN (SELECT i.product_id,i.price,o.shipping_country,o.created,SUM(IFNULL(i.quantity,0)) AS num FROM orders_orderitem AS i LEFT JOIN orders_order AS o ON i.order_id = o.id WHERE o.is_active=1 AND o.payment_status IN ('success', 'verify_pass') AND i.product_id IN "+ str(product_ids)+" GROUP BY o.shipping_country, i.product_id, i.price ) AS oi ON p.id = oi.product_id WHERE p.id in "+str(product_ids)

            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            response, writer = write_csv('export_sku_sale') 
            writer.writerow(['SKU',u'上架时间',u'销量',u'销售额',u'原价',u'现价(售出时现价)',u'成本价',u'毛利额',u'毛利率',u'国家'])

            std_field = ['sku','display_date','pprice','price','cost','shipping_country','num']

            for row in results:
                res = zip(std_field,row)
                res = dict(res)

                display_date = ''
                try:
                    display_date = time_str2(int(res['display_date']))
                except Exception as e:
                    print e
                    display_date = ''

                #销售额
                sales_amount = ''
                try:
                    sales_amount = int(res['num'])*float(res['price'])
                except Exception as e:
                    print e
                    sales_amount = ''

                #利润率：（现售价-美金成本）/现售价
                profit_rate = ''
                try:
                    profit_rate = (float(res['price']) - float(res['cost']))/float(res['price'])
                except Exception as e:
                    print e
                    profit_rate = ''

                #利润额：现售价-美金成本
                profit_margin  = '' 
                try:
                    profit_margin = (float(res['price']) - float(res['cost']))*int(res['num'])
                except Exception as e:
                    print e
                    profit_margin = '' 
                
                row = [
                    str(res['sku']),
                    str(display_date),
                    str(res['num']),
                    str(sales_amount),   #销售额
                    str(res['pprice']), #原价
                    str(res['price']),  #售价
                    str(res['cost']),   #成本
                    str(profit_margin),
                    str(profit_rate),
                    str(res['shipping_country']),
                ]

                writer.writerow(row)

            return response

    #网站所有sku表现情况导出
    elif request.POST.get('type') == 'export_skus_all':
        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)

        to_time = request.POST.get('to_time', '')

        if not to_time:
            messages.error(request, u'请选择时间作为当前日期')
            return redirect('product_sale')

        try:
            to_time = eparse(to_time, offset=" 23:59:59")
            to_time = time_stamp(to_time)
        except Exception as e:
            print e
            messages.error(request, u'请输入正确的时间格式时间')
            return redirect('product_sale')


        #当前时间
        # now = int(time.time())
        now = to_time
        # now = 1461031494

        #当前日期前一周开始时间
        last_week = now - 7*86400

        #当前日期前两周开始时间
        last_week_before = now - 2*7*86400

        #当前日期前三周开始时间
        three_week_before = now - 3*7*86400

        
        visibility = request.POST.get('visibility')
        sql_vis = ''
        if int(visibility) == 1:
            sql_vis = "p.visibility = 1"
        elif int(visibility) == 0:
            sql_vis = "p.visibility = 0"
        else:
            sql_vis = "p.visibility in (0, 1)"


        # sql = "SELECT p.id, p.sku,p.display_date, oi.num2, oi.num1,p.visibility,p.price,p.cost,p.type,p.source,p.stock FROM products_product AS p LEFT JOIN (SELECT oi2.product_id,oi2.num2,oi1.num1 FROM (SELECT i.product_id, SUM(IFNULL(i.quantity,0)) AS num2 FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 AND o.created > "+str(last_week_before)+" AND o.created < "+str(now)+" GROUP BY i.product_id) AS oi2  LEFT JOIN ( SELECT i.product_id, SUM(IFNULL(i.quantity,0)) AS num1 FROM orders_orderitem AS i  INNER JOIN orders_order AS o ON i.order_id = o.id  WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 AND o.created > "+str(last_week)+"  AND o.created < "+str(now)+" GROUP BY  i.product_id ) AS oi1 ON oi2.product_id = oi1.product_id) AS oi ON p.id = oi.product_id WHERE "+str(sql_vis)+" AND p.display_date < "+str(now)+"  GROUP BY p.sku"

        sql = "SELECT p.id, p.sku, p.display_date, oi.num3, oi.num2, oi.num1, p.visibility, p.price, p.cost, p.type, p.source, p.stock FROM products_product AS p LEFT JOIN (SELECT oi3.product_id, oi3.num3, oi12.num2, oi12.num1 FROM ( SELECT i.product_id, SUM(IFNULL(i.quantity, 0)) AS num3 FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 AND o.created > "+str(three_week_before)+" AND o.created < "+str(now)+" GROUP BY i.product_id ) AS oi3 LEFT JOIN ( SELECT oi2.product_id, oi2.num2, oi1.num1 FROM ( SELECT i.product_id,  SUM(IFNULL(i.quantity, 0)) AS num2 FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id  WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1  AND o.created > "+str(last_week_before)+" AND o.created < "+str(now)+" GROUP BY i.product_id ) AS oi2 LEFT JOIN ( SELECT i.product_id, SUM(IFNULL(i.quantity, 0)) AS num1  FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 AND o.created > "+str(last_week)+" AND o.created < "+str(now)+" GROUP BY i.product_id ) AS oi1 ON oi2.product_id = oi1.product_id GROUP BY oi2.product_id) AS oi12 ON oi12.product_id = oi3.product_id GROUP BY oi3.product_id) AS oi ON p.id = oi.product_id WHERE p.visibility = 1 AND p.display_date < "+str(now)+"  GROUP BY p.sku"

        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        response, writer = write_csv('export_sku_all') 
        writer.writerow(['SKU',u'上架时间',u'当前日期前三周销量',u'当前日期前两周销量',u'当前日期前一周销量',u'是否可见',u'网站现售价',u'成本价',u'毛利额',u'毛利率',u'现有库存量',u'产品类型',u'Source'])

        std_field = ['product_id','sku','display_date','num3','num2','num1','visibility','pprice','cost','type','source','stock']

        for row in results:
            res = zip(std_field,row)
            res = dict(res)

            display_date = ''
            try:
                display_date = time_str2(int(res['display_date']))
            except Exception as e:
                print e
                display_date = ''

            if res['visibility'] == 1:
                visibility = u'可见'
            else:
                visibility = u'不可见'

            #调用接口，获取产品现售价
            # url = settings.BASE_URL+'adminapi/product_sale_price'
            # url = 'http://local.oldchoies.com/adminapi/product_sale_price'
            # req = urllib2.Request(url)
            # response = urllib2.urlopen(req,urllib.urlencode({'product_id':res['product_id']})).read()
            # sale_price = response.strip('[]')
            cache_key = 'product_price_for_admin_'+str(res['product_id'])
            
            try:
                pprice = cache.get(cache_key)
            except Exception as e:
                pprice = res['pprice']

            if pprice == None:
                pprice = res['pprice']


            #利润率：（现售价-美金成本）/现售价
            profit_rate = ''
            try:
                profit_rate = (float(pprice) - float(res['cost']))/float(pprice)
            except Exception as e:
                print e
                profit_rate = ''

            #利润额：现售价-美金成本
            profit_margin  = '' 
            try:
                profit_margin = (float(pprice) - float(res['cost']))
            except Exception as e:
                print e
                profit_margin = '' 

            #产品类型
            try:
                res['type'] = int(res['type'])
            except Exception as e:
                res['type'] = res['type']

            if res['type'] == 1:
                ptype = u'配置产品'
            elif res['type'] == 2:
                ptype = u'打包产品'
            elif res['type'] == 3:
                ptype = u'简单配置产品'
            else:
                ptype = u'基本产品'

            #产品库存
            res['stock'] = str(res['stock'])

            if res['stock'] == '-1':
                stocks = Productitem.objects.filter(product_id=res['product_id']).aggregate(Sum("stock"))
                if stocks:
                    stock = stocks['stock__sum']
                else:
                    stock = 0
            elif res['stock'] == '0':
                stock = u'不可售'
            else:
                stock = u'不限制'

            #销量
            if str(res['num3']) == 'None':
                num3 = 0
            else:
                num3 = res['num3']

            if str(res['num2']) == 'None':
                num2 = 0
            else:
                num2 = res['num2']

            if str(res['num1']) == 'None':
                num1 = 0
            else:
                num1 = res['num1']

            row = [
                str(res['sku']),
                str(display_date),
                str(num3 - num2),
                str(num2 - num1),
                str(num1),
                str(visibility),
                str(pprice),
                str(res['cost']),
                str(profit_margin),
                str(profit_rate),
                str(stock),
                str(ptype),
                str(res['source']),
            ]

            writer.writerow(row)

        return response

    #各国品类销售统计表
    elif request.POST.get('type') == 'export_set_country_sale':
        from_time = request.POST.get('from_time', '')
        to_time = request.POST.get('to_time', '')

        if not from_time or not to_time:
            messages.error(request, u'请选择时间')
            return redirect('product_sale')

        try:
            from_time = eparse(from_time, offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(to_time, offset=" 23:59:59")
            to_time = time_stamp(to_time)
        except Exception as e:
            print e
            messages.error(request, u'请输入正确的时间格式时间')
            return redirect('product_sale')


        sql_time = " AND o.created > "+str(from_time)+" AND o.created < "+str(to_time)

        set_id = int(request.POST.get('set_id'))
        set_sql = ''
        if set_id == 0:
            set_sql = "  p.set_id IS NOT NULL  "
        else:
            set_sql = "  p.set_id = " + str(set_id)

        isocode = request.POST.get('isocode')
        country_sql = ''
        if isocode == 'all':
            country_sql = " AND o.shipping_country IS NOT NULL "
        else:
            country_sql = " AND o.shipping_country = '" + str(isocode) +"' "

        sql = "SELECT s.name,po.shipping_country,po.num,po.amount FROM products_set AS s INNER JOIN (SELECT p.set_id,oi.shipping_country,SUM(IFNULL(oi.num,0)) AS num,SUM(IFNULL(oi.price,0)* IFNULL(oi.num,0)) AS amount FROM products_product AS p INNER JOIN ( SELECT i.product_id, i.price, o.shipping_country, SUM(IFNULL(i.quantity,0)) AS num FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+str(country_sql)+str(sql_time)+" GROUP BY o.shipping_country, i.product_id, i.price) AS oi ON p.id = oi.product_id WHERE "+str(set_sql)+" GROUP BY p.set_id,oi.shipping_country) as po ON po.set_id = s.id"

        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        response, writer = write_csv('export_set_sale') 
        writer.writerow([u'品类',u'国家',u'销量',u'销售额'])

        std_field = ['name','shipping_country','num','amount']

        for row in results:
            res = zip(std_field,row)
            res = dict(res)

            row = [
                str(res['name']),
                str(res['shipping_country']),
                str(res['num']),
                str(res['amount']),
            ]

            writer.writerow(row)

        return response

    #新品动销统计表
    elif request.POST.get('type') == 'export_new_product_sale':
        from_time = request.POST.get('from_time', '')
        to_time = request.POST.get('to_time', '')

        if not from_time or not to_time:
            messages.error(request, u'请选择时间')
            return redirect('product_sale')

        try:
            from_time = eparse(from_time, offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(to_time, offset=" 23:59:59")
            to_time = time_stamp(to_time)
        except Exception as e:
            print e
            messages.error(request, u'请输入正确的时间格式时间')
            return redirect('product_sale')



        #该时间段内的上新产品
        products = Product.objects.filter(display_date__gte=from_time,display_date__lt=to_time).all()

        #上新数量
        new_count = products.count()

        sql = "SELECT p.sku FROM products_product AS p INNER JOIN ( SELECT i.product_id FROM  orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 AND o.created > "+str(from_time)+"  AND o.created < "+str(to_time)+"  GROUP BY i.product_id) AS oi ON p.id = oi.product_id WHERE  p.display_date > "+str(from_time)+"  AND p.display_date < "+str(to_time)+"  GROUP BY p.sku"

        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        new_sale_count = len(results)

        response, writer = write_csv('export_set_sale') 
        writer.writerow([u'动销SKU',u'动销SKU数量',u'上新数量',u'动销率'])

        if len(results) > 0:
            result1 = results[0]

            row = [
                str(result1[0]),
                str(new_sale_count),
                str(new_count),
                str(round(float(new_sale_count)/float(new_count),3)),
            ]
            writer.writerow(row)

            if len(results) > 1:
                result2 = results[1:]

                for res in result2:

                    row = [
                        str(res[0]),
                        str(''),
                        str(''),
                        str(''),
                    ]
                    writer.writerow(row)

        return response

    #各国家sku销售统计表
    elif request.POST.get('type') == 'export_sku_country_sale':

        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)

        from_time = request.POST.get('from_time', '')
        to_time = request.POST.get('to_time', '')

        if not from_time or not to_time:
            messages.error(request, u'请选择时间')
            return redirect('product_sale')

        try:
            from_time = eparse(from_time, offset=" 00:00:00")
            from_time = time_stamp(from_time)
            to_time = eparse(to_time, offset=" 23:59:59")
            to_time = time_stamp(to_time)
        except Exception as e:
            print e
            messages.error(request, u'请输入正确的时间格式时间')
            return redirect('product_sale')

        #当前时间为所选日期的结束时间
        # now = int(time.time())
        now = to_time
        # now = 1461031494

        #当前日期前一周开始时间
        last_week = now - 7*86400

        #当前日期前两周开始时间
        last_week_before = now - 2*7*86400

        isocode = request.POST.get('isocode')
        country_sql = ''
        if isocode == 'all':
            country_sql = " AND o.shipping_country IS NOT NULL "
        else:
            country_sql = " AND o.shipping_country = '" + str(isocode) +"' "

        #用开始时间和当前日期前两周的时间比较，时间小的放在left join的左边
        if from_time < last_week_before:
            sql = "SELECT p.id, p.sku, p.display_date, oi.num, oi.num2, oi.num1, oi.shipping_country, p.visibility, p.price, p.cost, p.type, p.source, p.stock FROM products_product AS p INNER JOIN (SELECT oit.product_id, oit.num, oit.shipping_country, oi12.num2, oi12.num1 FROM ( SELECT i.product_id, SUM(IFNULL(i.quantity, 0)) AS num, o.shipping_country FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(from_time)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oit LEFT JOIN ( SELECT oi2.product_id, oi2.num2, oi1.num1 FROM ( SELECT i.product_id,  SUM(IFNULL(i.quantity, 0)) AS num2  FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(last_week_before)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oi2 LEFT JOIN ( SELECT  i.product_id, SUM(IFNULL(i.quantity, 0)) AS num1 FROM  orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(last_week)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oi1 ON oi2.product_id = oi1.product_id ) AS oi12 ON oit.product_id = oi12.product_id GROUP BY oit.product_id) AS oi ON p.id = oi.product_id WHERE p.display_date < "+str(to_time)+" GROUP BY p.id"
        else:
            sql = "SELECT p.id, p.sku, p.display_date, oi.num, oi.num2, oi.num1, oi.shipping_country, p.visibility, p.price, p.cost, p.type, p.source, p.stock FROM products_product AS p INNER JOIN (SELECT oi12.product_id, oit.num, oi12.shipping_country, oi12.num2, oi12.num1 FROM ( SELECT oi2.product_id,oi2.shipping_country, oi2.num2, oi1.num1 FROM ( SELECT i.product_id,  SUM(IFNULL(i.quantity, 0)) AS num2,o.shipping_country  FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(last_week_before)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oi2 LEFT JOIN ( SELECT  i.product_id, SUM(IFNULL(i.quantity, 0)) AS num1 FROM  orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(last_week)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oi1 ON oi2.product_id = oi1.product_id ) AS oi12 LEFT JOIN ( SELECT i.product_id, SUM(IFNULL(i.quantity, 0)) AS num, o.shipping_country FROM orders_orderitem AS i INNER JOIN orders_order AS o ON i.order_id = o.id WHERE o.payment_status IN ('success', 'verify_pass') AND o.is_active = 1 "+country_sql+" AND o.created > "+str(from_time)+" AND o.created < "+str(to_time)+" GROUP BY i.product_id ) AS oit ON oit.product_id = oi12.product_id GROUP BY oi12.product_id) AS oi ON p.id = oi.product_id WHERE p.display_date < "+str(to_time)+" GROUP BY p.id"

        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        std_field1 = ['product_id','sku','display_date','num','num2','num1','shipping_country','visibility','pprice','cost','type','source','stock']

        response, writer = write_csv('export_sku_country') 
        writer.writerow([u'国家','SKU',u'所选日期内销量',u'当前日期前两周销量',u'当前日期前一周销量',u'是否可见',u'原价',u'网站现售价',u'成本价',u'毛利额',u'毛利率',u'现有库存量',u'产品类型',u'Source'])

        for row in results:
            res = zip(std_field1,row)
            res = dict(res)

            if res['visibility'] == 1:
                visibility = u'可见'
            else:
                visibility = u'不可见'

            # pprice = res['pprice']
            cache_key = 'product_price_for_admin_'+str(res['product_id'])
            
            try:
                pprice = cache.get(cache_key)
            except Exception as e:
                pprice = res['pprice']

            if pprice == None:
                pprice = res['pprice']


            #利润率：（现售价-美金成本）/现售价
            profit_rate = ''
            try:
                profit_rate = (float(pprice) - float(res['cost']))/float(pprice)
            except Exception as e:
                print e
                profit_rate = ''

            #利润额：现售价-美金成本
            profit_margin  = '' 
            try:
                profit_margin = (float(pprice) - float(res['cost']))
            except Exception as e:
                print e
                profit_margin = '' 

            #产品类型
            try:
                res['type'] = int(res['type'])
            except Exception as e:
                res['type'] = res['type']

            if res['type'] == 1:
                ptype = u'配置产品'
            elif res['type'] == 2:
                ptype = u'打包产品'
            elif res['type'] == 3:
                ptype = u'简单配置产品'
            else:
                ptype = u'基本产品'

            #产品库存
            res['stock'] = str(res['stock'])

            if res['stock'] == '-1':
                stocks = Productitem.objects.filter(product_id=res['product_id']).aggregate(Sum("stock"))
                if stocks:
                    stock = stocks['stock__sum']
                else:
                    stock = 0
            elif res['stock'] == '0':
                stock = u'不可售'
            else:
                stock = u'不限制'

            #销量
            if str(res['num2']) == 'None':
                num2 = 0
            else:
                num2 = res['num2']

            if str(res['num1']) == 'None':
                num1 = 0
            else:
                num1 = res['num1']

            if str(res['num']) == 'None':
                num = 0
            else:
                num = res['num']


            row = [
                str(res['shipping_country']),
                str(res['sku']),
                str(num),
                str(num2 - num1),
                str(num1),
                str(visibility),
                str(res['pprice']),
                str(pprice),
                str(res['cost']),
                str(profit_margin),
                str(profit_rate),
                str(stock),
                str(ptype),
                str(res['source']),
            ]

            writer.writerow(row)

        return response

    return HttpResponse('22222')


def sale_price_memcache(request):

    cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
    cache_key = 'memcache_test'
    cache_content = cache.get(cache_key)
    print cache_content
    return HttpResponse(cache_content)

    products = Product.objects.filter(visibility=1).all()
    for product in products:
        #调用接口，获取产品现售价
        # url = settings.BASE_URL+'adminapi/product_sale_price'
        url = 'http://local.oldchoies.com/adminapi/product_sale_price'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req,urllib.urlencode({'product_id':product.id})).read()
        sale_price = response.strip('[]')

        cache = memcache.Client([settings.MEMCACHE_URL],debug=0)
        cache_key = str(product.id)
        cache_data = sale_price
        cache.set(cache_key,cache_data,15*24*60*60)
        
    print products.count()

    messages.success(request, u'同步成功')
    return redirect('product_sale')