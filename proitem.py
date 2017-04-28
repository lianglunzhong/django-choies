# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone

# 独立执行的django脚本, 需要添加这四行
import sys, os, django

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from django.contrib.auth.models import User
from products.models import Product, Productitem

path = os.getcwd()
file2 = 'product_liu215.csv'  # D:\mywork\coding\latte\category.csv

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)


def isset(v):
    try:
        type(eval(v))
    except:
        return 0
    else:
        return 1


data_list = []
for row in reader:
    row[0] = row[0].strip().capitalize()
    row[1] = row[1].strip().capitalize()
    if len(row) < 3:
        row.append('')
        row.append('')
    if len(row) == 3:
        row.append('')
    tmp_dict = {"one": row[0], "two": row[1], "three": row[2], "four": row[3]}
    data_list.append(tmp_dict)
# print data_list
# exit()


n = 0
for i in range(len(data_list)):
    n = n + 1

    # print data_list[i],type(data_list[i])
    if data_list[i]['three'] != '':
        sku = data_list[i]['three']
    else:
        sku = data_list[i]['two']

    pro = Product.objects.filter(sku=sku).first()
    if pro:
        pro_id = Product.objects.filter(sku=sku).values('id', 'status', 'visibility','stock').first()
        if pro_id['status'] == 1 and pro_id['visibility'] == 1:
            status = 1
        else:
            status = 0
        if pro_id['stock'] == -99:
            stock = 9999
        else:
            stock = 100
        if pro_id['id']:
            pro_item = Productitem()
            if data_list[i]['four'] != '':
                item_sku = data_list[i]['four'].split('#')
                for i in range(len(item_sku)):
                    skuarr = item_sku[i]
                    (sku, size) = skuarr.split('!', 1)
                    pro_item = Productitem()
                    pro_item.product_id = pro_id['id']
                    pro_item.attribute = size
                    pro_item.stock = stock
                    pro_item.status = status
                    pro_item.sku = sku
                    pro_item.save()

print n

                # print row
                # exit()
                # return false
                # if len(row) > 3:
                # 	data_list[2] = row[2]
                # else:
                # 	data_list[2] = row[1]
                # row[3]=row[3].strip().capitalize()


                # print row[0]
                # tmp_dict={"before":row[0],"first":row[3],"second":row[2],}
                # if row[2]!=row[1]:
                #     tmp_dict["third"]=row[1]
                # data_list.append(tmp_dict)

# for i in range(len(data_list)):
#     if i==0:
#         continue
#     # print data_list[i]

#     c1, created1 = product.models.Category.objects.get_or_create(name=data_list[i]["first"],level=0,code=1,manager_id=1,parent_id__isnull=True)
#     c2, created2 = product.models.Category.objects.get_or_create(name=data_list[i]["second"],level=1,code=1,manager_id=1,parent=c1)
#     if "third" in data_list[i]:
#         c3, created3 = product.models.Category.objects.get_or_create(name=data_list[i]["third"],level=2,code=1,manager_id=1,parent=c2)

#     if "third" in data_list[i]:
#         cx=c3
#     else:
#         cx=c2

#     bri=cx.brief
#     if len(bri)==0:
#         cx.brief=bri+data_list[i]["before"]
#     else:
#         cx.brief=bri+';'+data_list[i]["before"]
#     cx.save()

handle.close()
