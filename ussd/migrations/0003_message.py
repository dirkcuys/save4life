# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-20 13:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ussd', '0002_auto_20161017_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to', models.CharField(max_length=1024)),
                ('body', models.CharField(max_length=160)),
                ('send_at', models.DateTimeField()),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
