# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diplomacy', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='canonicalorder',
            name='user_issued',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='canonicalorder',
            name='via_convoy',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='via_convoy',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
