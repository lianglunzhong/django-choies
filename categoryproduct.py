# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django,csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import CategoryProduct

path = os.getcwd()
file2 = 'categoryproduct1.csv'

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)
n = 0
m = 0
for row in reader:
    sin = CategoryProduct.objects.filter(category_id=row[3],product_id=row[4]).first()
    if not sin:
        n = n + 1
        CategoryProduct.objects.create(position=row[0],positiontwo=row[1],deleted=row[2],category_id=row[3],product_id=row[4])
    else:
        m = m + 1
        pass
print u'插入'+str(n)
print u'已存在：'+str(m)