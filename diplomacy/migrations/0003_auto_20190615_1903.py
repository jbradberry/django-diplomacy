# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-15 23:03
# flake8: noqa
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diplomacy', '0002_auto_20190610_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diplomacy_games', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='government',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
