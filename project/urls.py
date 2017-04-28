"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from products import views as products_views
from orders import views as orders_views
from django.views import static
from carts.views import ProductAutocomplete,CelebritsAutocomplete,FilterAutocomplete,CategoryAllAutocomplete,ProductitemAutocomplete,CustomerCouponsAutocomplete

urlpatterns = [

    url(r'^$', products_views.index, name='index'),
    url(r'^product-autocomplete/$', ProductAutocomplete.as_view(), name='product-autocomplete'),
    url(r'^celebrits-autocomplete/$', CelebritsAutocomplete.as_view(), name='celebrits-autocomplete'),
    url(r'^filter-autocomplete/$', FilterAutocomplete.as_view(), name='filter-autocomplete'),
    url(r'^categoryAll-autocomplete/$', CategoryAllAutocomplete.as_view(), name='categoryAll-autocomplete'),
    url(r'^productitem-autocomplete/$', ProductitemAutocomplete.as_view(), name='productitem-autocomplete'),
    url(r'^CustomerCoupons-autocomplete/$', CustomerCouponsAutocomplete.as_view(), name='CustomerCoupons-autocomplete'),
    url(r'^products/', include('products.urls')),
    url(r'^core/', include('core.urls')),
    url(r'^orders/', include('orders.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^carts/', include('carts.urls')),
    url(r'^celebrities/', include('celebrities.urls')),
    url(r'^about/$', TemplateView.as_view(template_name="about.html")),
    url(r'^admin/', admin.site.urls),
    url(r'^dashboard/$', orders_views.dashboard, name='dashboard'),
    # url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_PATH}),
    url(r'^site_media/(?P<path>[\S]+)$', static.serve,{'document_root': settings.STATIC_PATH}),
]
