# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django import forms
from django.forms import ModelForm

from products.models import *
from .models import CartItem,Spromotions
from dal import autocomplete
from celebrities.models import Celebrits
from carts.models import CustomerCoupons
class CartItemForm(forms.ModelForm):
    # item = forms.ModelChoiceField(
    #       queryset=Product.objects.all(),
 #          widget=autocomplete.ModelSelect2(url='product-autocomplete')
    #   )

    class Meta:
        model = Product
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'item': autocomplete.ModelSelect2(url='product-autocomplete'),
                }


class SpromotionsForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                }



class ProductAttributeForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                }



class FilterForm(forms.ModelForm):

    class Meta:
        model = Filter
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'filter': autocomplete.ModelSelect2(url='filter-autocomplete'),
                }

class CelebrityImagesForm(forms.ModelForm):

    class Meta:
        model = Celebrits
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'celebrity': autocomplete.ModelSelect2(url='celebrits-autocomplete'),
                }

class ProductTransForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                }

class CategoryAllForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'parent': autocomplete.ModelSelect2(url='categoryAll-autocomplete'),
                }

class ProductCategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'category': autocomplete.ModelSelect2(url='categoryAll-autocomplete'),
                }


class ProductitemForm(ModelForm):

    class Meta:
        model = Productitem
        fields = '__all__'
        widgets = {
                'item': autocomplete.ModelSelect2(url='productitem-autocomplete'),
                }
class CustomerCouponsForm(ModelForm):

    class Meta:
        model = CustomerCoupons
        fields = '__all__'
        widgets = {
                'customer': autocomplete.ModelSelect2(url='CustomerCoupons-autocomplete'),
                }