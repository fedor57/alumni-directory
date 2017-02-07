# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-06 23:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20170206_0658'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authcode',
            name='owner_name',
        ),
        migrations.AddField(
            model_name='authcode',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Student'),
        ),
    ]