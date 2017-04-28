# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Productitem,Product
import csv

path = os.getcwd()
file2 = 'product216.csv'

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)


data_list = []
n = 0
for row in reader:
    if len(row) < 3:
        row.append('')
        row.append('')
        row.append('')
        row.append('')

    elif len(row) < 6:
        row.append('')
    n = n + 1
    if len(row) != 6:
        # print row
        print u'第 %d 行有错误' % n
        exit()
    # print row[0]
    r = ['','','','','','']
    r[0] = row[0].strip()
    r[1] = row[1].strip()
    r[2] = row[2].strip()
    r[3] = row[5].strip()
    tmp_dict = {"one": r[0], "two": r[1], "three": r[2], "four": r[3]}
    data_list.append(tmp_dict)
print n
# print data_list
# exit()

n = 0

for i in range(len(data_list)):
    if data_list[i]['one'] != 'not':
        if data_list[i]['three'] != '':
            sku = data_list[i]['three']
        else:
            sku = data_list[i]['two']
        pro = Product.objects.filter(sku=sku).first()
        if pro:
            items = Productitem.objects.filter(product_id=pro.id).values('id','sku','attribute')
            if items:
                item_sku = data_list[i]['four'].split('#')
                # Productitem.objects.filter(product_id=pro.id).update(status=0)
                for item in items:
                    if item['sku'] in item_sku:
                        # print item['sku']
                        if pro.status==1:
                            n = n + 1
                            # Productitem.objects.filter(id=item['id']).update(status=1)
print  n
