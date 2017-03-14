# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from ..engine import standard


def subregion_key(sr):
    if not sr:
        return None
    return (sr.territory.name, sr.subname, sr.sr_type)


class Migration(DataMigration):

    def forwards(self, orm):
        inv_powers = {v: k for k, v in standard.powers.iteritems()}
        inv_territories = {v: k for k, v in standard.territories.iteritems()}
        inv_subregions = {v: k for k, v in standard.subregions.iteritems()}

        for g in orm.Government.objects.all():
            g.power_name = inv_powers.get(g.power.name, '')
            g.save()

        for o in orm.Ownership.objects.all():
            o.territory_name = inv_territories[o.territory.name]
            o.save()

        for u in orm.Unit.objects.all():
            u.subregion_name = inv_subregions[subregion_key(u.subregion)]
            u.previous_name = inv_subregions.get(subregion_key(u.previous.subregion), '')
            u.displaced_from_name = inv_territories.get(u.displaced_from.name, '')
            u.standoff_from_name = inv_territories.get(u.standoff_from.name, '')
            u.save()

        for o in orm.Order.objects.all():
            o.actor_name = inv_subregions[subregion_key(o.actor)]
            o.assist_name = inv_subregions.get(subregion_key(o.assist), '')
            o.target_name = inv_subregions.get(subregion_key(o.target), '')
            o.save()

        for o in orm.CanonicalOrder.objects.all():
            o.actor_name = inv_subregions[subregion_key(o.actor)]
            o.assist_name = inv_subregions.get(subregion_key(o.assist), '')
            o.target_name = inv_subregions.get(subregion_key(o.target), '')
            o.save()

    def backwards(self, orm):
        pass

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'diplomacy.canonicalorder': {
            'Meta': {'object_name': 'CanonicalOrder'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'canonical_actor'", 'to': u"orm['diplomacy.Subregion']"}),
            'actor_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'canonical_assist'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'assist_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'canonical_target'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'target_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"}),
            'user_issued': ('django.db.models.fields.BooleanField', [], {}),
            'via_convoy': ('django.db.models.fields.BooleanField', [], {})
        },
        u'diplomacy.diplomacyprefs': {
            'Meta': {'object_name': 'DiplomacyPrefs'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'warnings': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'diplomacy.game': {
            'Meta': {'object_name': 'Game'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'open_joins': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'diplomacy_games'", 'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'})
        },
        u'diplomacy.government': {
            'Meta': {'object_name': 'Government'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owns': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['diplomacy.Territory']", 'through': u"orm['diplomacy.Ownership']", 'symmetrical': 'False'}),
            'power': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Power']", 'null': 'True', 'blank': 'True'}),
            'power_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'diplomacy.order': {
            'Meta': {'object_name': 'Order'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'acts'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'actor_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assisted'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'assist_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': u"orm['diplomacy.OrderPost']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'targeted'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'target_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'via_convoy': ('django.db.models.fields.BooleanField', [], {})
        },
        u'diplomacy.orderpost': {
            'Meta': {'ordering': "('timestamp',)", 'object_name': 'OrderPost'},
            'government': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['diplomacy.Turn']"})
        },
        u'diplomacy.ownership': {
            'Meta': {'unique_together': "(('turn', 'territory'),)", 'object_name': 'Ownership'},
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'territory': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Territory']"}),
            'territory_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"})
        },
        u'diplomacy.power': {
            'Meta': {'object_name': 'Power'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'diplomacy.subregion': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Subregion'},
            'borders': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'borders_rel_+'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_unit': ('django.db.models.fields.BooleanField', [], {}),
            'sr_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'subname': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'territory': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Territory']"})
        },
        u'diplomacy.territory': {
            'Meta': {'object_name': 'Territory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_supply': ('django.db.models.fields.BooleanField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'power': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Power']", 'null': 'True', 'blank': 'True'})
        },
        u'diplomacy.turn': {
            'Meta': {'ordering': "('-generated',)", 'object_name': 'Turn'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Game']"}),
            'generated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'season': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'diplomacy.unit': {
            'Meta': {'ordering': "('-turn', 'government', 'subregion')", 'object_name': 'Unit'},
            'dislodged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'displaced_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'displaced'", 'null': 'True', 'to': u"orm['diplomacy.Territory']"}),
            'displaced_from_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'previous': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Unit']", 'null': 'True', 'blank': 'True'}),
            'previous_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'standoff_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'standoff'", 'null': 'True', 'to': u"orm['diplomacy.Territory']"}),
            'standoff_from_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Subregion']"}),
            'subregion_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"}),
            'u_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['diplomacy']
    symmetrical = True
