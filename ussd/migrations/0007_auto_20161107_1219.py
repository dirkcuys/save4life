# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-07 12:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ussd', '0006_quiz_description'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='quiz',
            options={'verbose_name_plural': 'quizzes'},
        ),
        migrations.AddField(
            model_name='quiz',
            name='name',
            field=models.CharField(default='Give me a name!', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='quiz',
            name='reminder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ussd.Message'),
        ),
    ]