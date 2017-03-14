# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Ownership', fields ['turn', 'territory_name']
        db.delete_unique(u'diplomacy_ownership', ['turn_id', 'territory_name'])

        db.rename_column(u'diplomacy_unit', 'previous_name', 'previous')

        db.rename_column(u'diplomacy_unit', 'subregion_name', 'subregion')

        db.rename_column(u'diplomacy_unit', 'standoff_from_name', 'standoff_from')

        db.rename_column(u'diplomacy_unit', 'displaced_from_name', 'displaced_from')

        db.rename_column(u'diplomacy_canonicalorder', 'actor_name', 'actor')

        db.rename_column(u'diplomacy_canonicalorder', 'target_name', 'target')

        db.rename_column(u'diplomacy_canonicalorder', 'assist_name', 'assist')

        db.rename_column(u'diplomacy_order', 'actor_name', 'actor')

        db.rename_column(u'diplomacy_order', 'assist_name', 'assist')

        db.rename_column(u'diplomacy_order', 'target_name', 'target')

        db.rename_column(u'diplomacy_ownership', 'territory_name', 'territory')

        # Adding unique constraint on 'Ownership', fields ['turn', 'territory']
        db.create_unique(u'diplomacy_ownership', ['turn_id', 'territory'])

        db.rename_column(u'diplomacy_government', 'power_name', 'power')


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
            'actor': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
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
            'power': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'diplomacy.order': {
            'Meta': {'object_name': 'Order'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'actor': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': u"orm['diplomacy.OrderPost']"}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
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
            'territory': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"})
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
            'displaced_from': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'previous': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'standoff_from': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subregion': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"}),
            'u_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['diplomacy']
