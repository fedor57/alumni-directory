# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-06 06:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20170118_0716'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='grade',
            options={'ordering': ('-graduation_year', 'letter'), 'verbose_name': '\u043a\u043b\u0430\u0441\u0441', 'verbose_name_plural': '\u043a\u043b\u0430\u0441\u0441\u044b'},
        ),
        migrations.AddField(
            model_name='fieldvalue',
            name='votes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fieldvalue',
            name='field_name',
            field=models.CharField(choices=[('name', '\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0444\u0430\u043c\u0438\u043b\u0438\u0438 / \u0438\u043c\u0435\u043d\u0438'), ('email', 'Email'), ('city', '\u0413\u043e\u0440\u043e\u0434'), ('company', '\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f / \u0412\u0423\u0417'), ('link', '\u0414\u043e\u043c\u0430\u0448\u043d\u044f\u044f \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430'), ('social_fb', 'Facebook'), ('social_vk', '\u0412\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u0435'), ('grade', '\u0423\u0447\u0438\u043b\u0441\u044f \u0442\u0430\u043a\u0436\u0435 \u0432 \u043a\u043b\u0430\u0441\u0441\u0435')], max_length=20, verbose_name='\u0418\u043c\u044f \u043f\u043e\u043b\u044f'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='field_value',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.FieldValue', verbose_name='\u041f\u043e\u043b\u0435'),
        ),
    ]
