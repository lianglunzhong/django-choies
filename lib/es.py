# coding: utf-8
from elasticsearch import Elasticsearch
from django.conf import settings
from products.models import Productitem,CategoryProduct


def es_update(product_id):
    es = Elasticsearch(settings.ES_URL)
    data = category_add(product_id)
    print product_id,data
    res = es.update(index=settings.ES_INDEX, doc_type='product_', id=product_id, body={'doc':data})
    return res

def category_add(product_id):
        attrs = Productitem.objects.filter(product_id=product_id).values("attribute").all()

        attr = {}
        if attrs:
            default_catalog = u''
            cp = CategoryProduct.objects.filter(product_id=product_id,category__visibility=1).values('category_id')
            if cp:
                for cid in cp:
                    default_catalog += str(cid['category_id']) + ' '

            attr['default_catalog'] = default_catalog
        else:
            attr['default_catalog'] = u''
        return attr