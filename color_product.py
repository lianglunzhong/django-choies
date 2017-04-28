# coding: utf-8

# 同步同款不同色的历史数据


# 独立执行的django脚本, 需要添加这四行
import sys, os, django,csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from products.models import Product,ColorProduct

path = os.getcwd()
file2 = 'catalog_colors.csv'

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)
data = {}
n = 0
products = Product.objects.values_list('sku','id')
for product in products:
    data[product[0]] = product[1]

for row in reader:
    product_id = data.get(row[0])
    if product_id:
        n = n + 1
        ColorProduct.objects.get_or_create(product_id=product_id,group=row[1])
print u'插入 %d 条数据' % n