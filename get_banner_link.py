# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from banners.models import Banner
from products.models import Product,  ProductAttribute
import phpserialize

#分类banner顺序调换

Banner.objects.filter(id=1387,type='phonecatalog',lang='').update(position=6)
Banner.objects.filter(id=1386,type='phonecatalog',lang='').update(position=7)
Banner.objects.filter(id=1381,type='phonecatalog',lang='').update(position=1)

banner_1305 = Banner.objects.filter(id=1305).first()

link_1305 = banner_1305.linkarray.strip().split(',')
image_map = phpserialize.loads(banner_1305.map.encode('utf8'))

i = 0
for key,value in image_map.items():
	query1,is_created1 = Banner.objects.get_or_create(link=link_1305[i],image=value,type='index8',position=i,lang='')
	i += 1
	print query1.id



banner_1306 = Banner.objects.filter(id=1306).first()

link_1306 = banner_1306.linkarray.strip().split(',')
image_map = phpserialize.loads(banner_1306.map.encode('utf8'))

i = 0
for key,value in image_map.items():
	query2,is_created2 = Banner.objects.get_or_create(link=link_1306[i],image=value,type='index6',position=i,lang='')
	i += 1
	print query2.id



banner_1307 = Banner.objects.filter(id=1307).first()

link_1307 = banner_1307.linkarray.strip().split(',')
image_map = phpserialize.loads(banner_1307.map.encode('utf8'))

i = 0
for key,value in image_map.items():
	query3,is_created3 = Banner.objects.get_or_create(link=link_1307[i],image=value,type='index12',position=i,lang='')
	i += 1
	print query3.id



#新增top_banner和产品页小banner
if 1:
	query,is_created = Banner.objects.get_or_create(link='/',image='',type='top_banner',position=0,lang='',visibility=0)
	query1,is_created1 = Banner.objects.get_or_create(link='/',image='',type='product_site',position=0,lang='',visibility=0)



'''

map_1305 = [
	u'左1-350x460_v1457917813.jpg',
	u'左2-350x180_v1457917823.jpg',
	u'中1-150x210_v1457917838.jpg',
	u'中2-150x210_v1457918013.jpg',
	u'中3-320x430_v1457918020.jpg',
	u'右1-320x430_v1457918026.jpg',
	u'右2-150x210_v1457918034.jpg',
	u'右3-150x210_v1457918396.jpg',
	]
i = 0
while i<8:
	query1,is_created1 = Banner.objects.get_or_create(link=link_1305[i],image=map_1305[i],type='index8',position=86,lang='')
	# query1_de,is_created1_de = Banner.objects.get_or_create(link=link_1305[i],image=map_1305[i],type='index8',position=86,lang='de',)
	# query1_fr,is_created1_fr = Banner.objects.get_or_create(link=link_1305[i],image=map_1305[i],type='index8',position=86,lang='fr')
	# query1_es,is_created1_es = Banner.objects.get_or_create(link=link_1305[i],image=map_1305[i],type='index8',position=86,lang='es')
	i +=1
	print query1.id


banner_1306 = Banner.objects.filter(id=1306).first()
link_1306 = banner_1306.linkarray.strip().split(',')

map_1306 = [
	u'DR000OPK_v1485052693.jpg',
	u'DR000OSD_v1485052699.jpg',
	u'DR000OPG_v1484648220.jpg',
	u'BS000OOZ_v1485052736.jpg',
	u'CJ000N50_v1481252327.jpg',
	u'HC000OPV_v1484648222.jpg',
]

i = 0
while i<6:
	query2,is_created2 = Banner.objects.get_or_create(link=link_1306[i],image=map_1306[i],type='index6',position=87,lang='')
	# query2_de,is_created2_de = Banner.objects.get_or_create(link=link_1306[i],image=map_1306[i],type='index6',position=87,lang='de',)
	# query2_fr,is_created2_fr = Banner.objects.get_or_create(link=link_1306[i],image=map_1306[i],type='index6',position=87,lang='fr')
	# query2_es,is_created2_es = Banner.objects.get_or_create(link=link_1306[i],image=map_1306[i],type='index6',position=87,lang='es')
	i +=1
	print query2.id


banner_1307 = Banner.objects.filter(id=1307).first()
link_1307 = banner_1307.linkarray.strip().split(',')

map_1307 = [
	u'COAT100614A008_v1481511683.jpg',
	u'09_v1474613493.jpg',
	u'未标题-1_v1479351577.jpg',
	u'CSAHFY_v1486175724.jpg',
	u'03_v1474613515.jpg',
	u'06_v1474613523.jpg',
	u'BLOU0529B628K_v1486175787.jpg',
	u'DR000L2I_v1481511720.jpg',
	u'12_v1474613543.jpg',
	u'未标题-2_v1479351648.jpg',
	u'hei_v1483409688.jpg',
	u'标题-1_v1485053463.jpg',
]

i = 0
while i<12:
	query3,is_created3 = Banner.objects.get_or_create(link=link_1307[i],image=map_1307[i],type='index12',position=88,lang='')
	# query3_de,is_created3_de = Banner.objects.get_or_create(link=link_1307[i],image=map_1307[i],type='index12',position=88,lang='de',)
	# query3_fr,is_created3_fr = Banner.objects.get_or_create(link=link_1307[i],image=map_1307[i],type='index12',position=88,lang='fr')
	# query3_es,is_created3_es = Banner.objects.get_or_create(link=link_1307[i],image=map_1307[i],type='index12',position=88,lang='es')
	i +=1
	print query3.id

#新增top_banner和产品页小banner
if 1:
	query,is_created = Banner.objects.get_or_create(link='/',image='',type='top_banner',position=0,lang='')
	query1,is_created1 = Banner.objects.get_or_create(link='/',image='',type='product_site',position=0,lang='')
'''