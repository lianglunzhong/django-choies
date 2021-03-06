# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-02-28 10:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('celebrities', '0001_initial'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_auto_20170228_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='celebrityorder',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.Order', verbose_name='\u8ba2\u5355ID'),
        ),
        migrations.AddField(
            model_name='celebrityfees',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Admin'),
        ),
        migrations.AddField(
            model_name='celebrityfees',
            name='celebrity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='celebrities.Celebrits', verbose_name='\u7ea2\u4ebaID'),
        ),
        migrations.AddField(
            model_name='celebritycontacted',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Admin'),
        ),
        migrations.AddField(
            model_name='celebritycontacted',
            name='celebrity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='celebrities.Celebrits', verbose_name='\u7ea2\u4ebaID'),
        ),
        migrations.AddField(
            model_name='celebrityblogs',
            name='celebrity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='celebrities.Celebrits', verbose_name='\u7ea2\u4ebaID'),
        ),
        migrations.AddField(
            model_name='celebrits',
            name='admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Admin'),
        ),
        migrations.AddField(
            model_name='celebrits',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Customers', verbose_name='\u7528\u6237ID'),
        ),
    ]
