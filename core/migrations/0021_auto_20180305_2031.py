# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-03-05 20:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20170923_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldvalue',
            name='status_update_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0443\u0441\u0430'),
        ),
    ]
