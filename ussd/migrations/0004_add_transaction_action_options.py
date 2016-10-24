# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-24 15:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ussd', '0003_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='action',
            field=models.CharField(choices=[('saving', 'saving'), ('withdrawal', 'withdrawal'), ('airtime', 'airtime'), ('rewards', 'rewards'), ('registration bonus', 'registration bonus')], max_length=12),
        ),
    ]
