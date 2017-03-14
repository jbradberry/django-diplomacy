# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Ownership', fields ['turn', 'territory']
        db.delete_unique(u'diplomacy_ownership', ['turn_id', 'territory_id'])

        # Deleting model 'Territory'
        db.delete_table(u'diplomacy_territory')

        # Deleting model 'Subregion'
        db.delete_table(u'diplomacy_subregion')

        # Removing M2M table for field borders on 'Subregion'
        db.delete_table(db.shorten_name(u'diplomacy_subregion_borders'))

        # Deleting model 'Power'
        db.delete_table(u'diplomacy_power')

        # Deleting field 'Ownership.territory'
        db.delete_column(u'diplomacy_ownership', 'territory_id')

        # Adding unique constraint on 'Ownership', fields ['turn', 'territory_name']
        db.create_unique(u'diplomacy_ownership', ['turn_id', 'territory_name'])

        # Deleting field 'Unit.subregion'
        db.delete_column(u'diplomacy_unit', 'subregion_id')

        # Deleting field 'Unit.displaced_from'
        db.delete_column(u'diplomacy_unit', 'displaced_from_id')

        # Deleting field 'Unit.previous'
        db.delete_column(u'diplomacy_unit', 'previous_id')

        # Deleting field 'Unit.standoff_from'
        db.delete_column(u'diplomacy_unit', 'standoff_from_id')

        # Deleting field 'CanonicalOrder.assist'
        db.delete_column(u'diplomacy_canonicalorder', 'assist_id')

        # Deleting field 'CanonicalOrder.target'
        db.delete_column(u'diplomacy_canonicalorder', 'target_id')

        # Deleting field 'CanonicalOrder.actor'
        db.delete_column(u'diplomacy_canonicalorder', 'actor_id')

        # Deleting field 'Order.assist'
        db.delete_column(u'diplomacy_order', 'assist_id')

        # Deleting field 'Order.target'
        db.delete_column(u'diplomacy_order', 'target_id')

        # Deleting field 'Order.actor'
        db.delete_column(u'diplomacy_order', 'actor_id')

        # Deleting field 'Government.power'
        db.delete_column(u'diplomacy_government', 'power_id')


    def backwards(self, orm):
        # Removing unique constraint on 'Ownership', fields ['turn', 'territory_name']
        db.delete_unique(u'diplomacy_ownership', ['turn_id', 'territory_name'])

        # Adding model 'Territory'
        db.create_table(u'diplomacy_territory', (
            ('power', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Power'], null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('is_supply', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'diplomacy', ['Territory'])

        # Adding model 'Subregion'
        db.create_table(u'diplomacy_subregion', (
            ('init_unit', self.gf('django.db.models.fields.BooleanField')()),
            ('subname', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('sr_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('territory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Territory'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'diplomacy', ['Subregion'])

        # Adding M2M table for field borders on 'Subregion'
        m2m_table_name = db.shorten_name(u'diplomacy_subregion_borders')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_subregion', models.ForeignKey(orm[u'diplomacy.subregion'], null=False)),
            ('to_subregion', models.ForeignKey(orm[u'diplomacy.subregion'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_subregion_id', 'to_subregion_id'])

        # Adding model 'Power'
        db.create_table(u'diplomacy_power', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'diplomacy', ['Power'])


        # User chose to not deal with backwards NULL issues for 'Ownership.territory'
        raise RuntimeError("Cannot reverse this migration. 'Ownership.territory' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Ownership.territory'
        db.add_column(u'diplomacy_ownership', 'territory',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Territory']),
                      keep_default=False)

        # Adding unique constraint on 'Ownership', fields ['turn', 'territory']
        db.create_unique(u'diplomacy_ownership', ['turn_id', 'territory_id'])


        # User chose to not deal with backwards NULL issues for 'Unit.subregion'
        raise RuntimeError("Cannot reverse this migration. 'Unit.subregion' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Unit.subregion'
        db.add_column(u'diplomacy_unit', 'subregion',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Subregion']),
                      keep_default=False)

        # Adding field 'Unit.displaced_from'
        db.add_column(u'diplomacy_unit', 'displaced_from',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='displaced', null=True, to=orm['diplomacy.Territory'], blank=True),
                      keep_default=False)

        # Adding field 'Unit.previous'
        db.add_column(u'diplomacy_unit', 'previous',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Unit'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Unit.standoff_from'
        db.add_column(u'diplomacy_unit', 'standoff_from',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='standoff', null=True, to=orm['diplomacy.Territory'], blank=True),
                      keep_default=False)

        # Adding field 'CanonicalOrder.assist'
        db.add_column(u'diplomacy_canonicalorder', 'assist',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='canonical_assist', null=True, to=orm['diplomacy.Subregion'], blank=True),
                      keep_default=False)

        # Adding field 'CanonicalOrder.target'
        db.add_column(u'diplomacy_canonicalorder', 'target',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='canonical_target', null=True, to=orm['diplomacy.Subregion'], blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'CanonicalOrder.actor'
        raise RuntimeError("Cannot reverse this migration. 'CanonicalOrder.actor' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'CanonicalOrder.actor'
        db.add_column(u'diplomacy_canonicalorder', 'actor',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='canonical_actor', to=orm['diplomacy.Subregion']),
                      keep_default=False)

        # Adding field 'Order.assist'
        db.add_column(u'diplomacy_order', 'assist',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='assisted', null=True, to=orm['diplomacy.Subregion'], blank=True),
                      keep_default=False)

        # Adding field 'Order.target'
        db.add_column(u'diplomacy_order', 'target',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='targeted', null=True, to=orm['diplomacy.Subregion'], blank=True),
                      keep_default=False)

        # Adding field 'Order.actor'
        db.add_column(u'diplomacy_order', 'actor',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='acts', null=True, to=orm['diplomacy.Subregion'], blank=True),
                      keep_default=False)

        # Adding field 'Government.power'
        db.add_column(u'diplomacy_government', 'power',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Power'], null=True, blank=True),
                      keep_default=False)


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
            'actor_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
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
            'power_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'diplomacy.order': {
            'Meta': {'object_name': 'Order'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'actor_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'assist_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': u"orm['diplomacy.OrderPost']"}),
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
            'Meta': {'unique_together': "(('turn', 'territory_name'),)", 'object_name': 'Ownership'},
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'territory_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
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
            'Meta': {'ordering': "('-turn', 'government', 'subregion_name')", 'object_name': 'Unit'},
            'dislodged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'displaced_from_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'previous_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'standoff_from_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subregion_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"}),
            'u_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['diplomacy']