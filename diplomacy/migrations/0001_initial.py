# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CanonicalOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('actor', models.CharField(max_length=64, blank=True)),
                ('action', models.CharField(blank=True, max_length=1, null=True, choices=[(b'H', b'Hold'), (b'M', b'Move'), (b'S', b'Support'), (b'C', b'Convoy'), (b'B', b'Build'), (b'D', b'Disband')])),
                ('assist', models.CharField(max_length=64, blank=True)),
                ('target', models.CharField(max_length=64, blank=True)),
                ('via_convoy', models.BooleanField()),
                ('user_issued', models.BooleanField()),
                ('result', models.CharField(max_length=1, choices=[(b'S', b'Succeeded'), (b'F', b'Failed'), (b'B', b'Bounced'), (b'D', b'Destroyed')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DiplomacyPrefs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('warnings', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'diplomacyprefs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(default=b'S', max_length=1, choices=[(b'S', b'Setup'), (b'A', b'Active'), (b'P', b'Paused'), (b'F', b'Finished')])),
                ('open_joins', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, related_name='diplomacy_games', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Government',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('power', models.CharField(max_length=32, blank=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Game')),
                ('user', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('actor', models.CharField(max_length=64, blank=True)),
                ('action', models.CharField(blank=True, max_length=1, null=True, choices=[(b'H', b'Hold'), (b'M', b'Move'), (b'S', b'Support'), (b'C', b'Convoy'), (b'B', b'Build'), (b'D', b'Disband')])),
                ('assist', models.CharField(max_length=64, blank=True)),
                ('target', models.CharField(max_length=64, blank=True)),
                ('via_convoy', models.BooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('government', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='diplomacy.Government')),
            ],
            options={
                'ordering': ('timestamp',),
                'get_latest_by': 'timestamp',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ownership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('territory', models.CharField(max_length=32, blank=True)),
                ('government', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Government')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('year', models.IntegerField()),
                ('season', models.CharField(max_length=2, choices=[(b'S', b'Spring'), (b'SR', b'Spring Retreat'), (b'F', b'Fall'), (b'FR', b'Fall Retreat'), (b'FA', b'Fall Adjustment')])),
                ('generated', models.DateTimeField(auto_now_add=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Game')),
            ],
            options={
                'ordering': ('-generated',),
                'get_latest_by': 'generated',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('u_type', models.CharField(max_length=1, choices=[(b'A', b'Army'), (b'F', b'Fleet')])),
                ('subregion', models.CharField(max_length=64, blank=True)),
                ('previous', models.CharField(max_length=64, blank=True)),
                ('dislodged', models.BooleanField(default=False)),
                ('displaced_from', models.CharField(max_length=32, blank=True)),
                ('standoff_from', models.CharField(max_length=32, blank=True)),
                ('government', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Government')),
                ('turn', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Turn')),
            ],
            options={
                'ordering': ('-turn', 'government', 'subregion'),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='ownership',
            name='turn',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Turn'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='ownership',
            unique_together=set([('turn', 'territory')]),
        ),
        migrations.AddField(
            model_name='orderpost',
            name='turn',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='diplomacy.Turn'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='diplomacy.OrderPost'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='canonicalorder',
            name='government',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Government'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='canonicalorder',
            name='turn',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diplomacy.Turn'),
            preserve_default=True,
        ),
    ]
