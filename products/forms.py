# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django import forms
from django.forms import ModelForm

from products.models import *
from dal import autocomplete

class CategoryProductForm(ModelForm):

    class Meta:
        model = CategoryProduct
        fields = '__all__'

        widgets = {
            'category': autocomplete.ModelSelect2(url='categoryAll-autocomplete'),
        }


