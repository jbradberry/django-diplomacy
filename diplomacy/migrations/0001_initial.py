# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DiplomacyPrefs'
        db.create_table(u'diplomacy_diplomacyprefs', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('warnings', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'diplomacy', ['DiplomacyPrefs'])

        # Adding model 'Game'
        db.create_table(u'diplomacy_game', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='diplomacy_games', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='S', max_length=1)),
            ('open_joins', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'diplomacy', ['Game'])

        # Adding model 'Turn'
        db.create_table(u'diplomacy_turn', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Game'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('season', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('generated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'diplomacy', ['Turn'])

        # Adding model 'Power'
        db.create_table(u'diplomacy_power', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'diplomacy', ['Power'])

        # Adding model 'Territory'
        db.create_table(u'diplomacy_territory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('power', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Power'], null=True, blank=True)),
            ('is_supply', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'diplomacy', ['Territory'])

        # Adding model 'Subregion'
        db.create_table(u'diplomacy_subregion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('territory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Territory'])),
            ('subname', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('sr_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('init_unit', self.gf('django.db.models.fields.BooleanField')()),
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

        # Adding model 'Government'
        db.create_table(u'diplomacy_government', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Game'])),
            ('power', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Power'], null=True, blank=True)),
        ))
        db.send_create_signal(u'diplomacy', ['Government'])

        # Adding model 'Ownership'
        db.create_table(u'diplomacy_ownership', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('turn', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Turn'])),
            ('government', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Government'])),
            ('territory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Territory'])),
        ))
        db.send_create_signal(u'diplomacy', ['Ownership'])

        # Adding unique constraint on 'Ownership', fields ['turn', 'territory']
        db.create_unique(u'diplomacy_ownership', ['turn_id', 'territory_id'])

        # Adding model 'Unit'
        db.create_table(u'diplomacy_unit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('turn', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Turn'])),
            ('government', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Government'])),
            ('u_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('subregion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Subregion'])),
            ('previous', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Unit'], null=True, blank=True)),
            ('dislodged', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('displaced_from', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='displaced', null=True, to=orm['diplomacy.Territory'])),
            ('standoff_from', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='standoff', null=True, to=orm['diplomacy.Territory'])),
        ))
        db.send_create_signal(u'diplomacy', ['Unit'])

        # Adding model 'OrderPost'
        db.create_table(u'diplomacy_orderpost', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('turn', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['diplomacy.Turn'])),
            ('government', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['diplomacy.Government'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'diplomacy', ['OrderPost'])

        # Adding model 'Order'
        db.create_table(u'diplomacy_order', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(related_name='orders', to=orm['diplomacy.OrderPost'])),
            ('actor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='acts', null=True, to=orm['diplomacy.Subregion'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('assist', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='assisted', null=True, to=orm['diplomacy.Subregion'])),
            ('target', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='targeted', null=True, to=orm['diplomacy.Subregion'])),
            ('via_convoy', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'diplomacy', ['Order'])

        # Adding model 'CanonicalOrder'
        db.create_table(u'diplomacy_canonicalorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('turn', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Turn'])),
            ('government', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diplomacy.Government'])),
            ('actor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='canonical_actor', to=orm['diplomacy.Subregion'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('assist', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='canonical_assist', null=True, to=orm['diplomacy.Subregion'])),
            ('target', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='canonical_target', null=True, to=orm['diplomacy.Subregion'])),
            ('via_convoy', self.gf('django.db.models.fields.BooleanField')()),
            ('user_issued', self.gf('django.db.models.fields.BooleanField')()),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal(u'diplomacy', ['CanonicalOrder'])


    def backwards(self, orm):
        # Removing unique constraint on 'Ownership', fields ['turn', 'territory']
        db.delete_unique(u'diplomacy_ownership', ['turn_id', 'territory_id'])

        # Deleting model 'DiplomacyPrefs'
        db.delete_table(u'diplomacy_diplomacyprefs')

        # Deleting model 'Game'
        db.delete_table(u'diplomacy_game')

        # Deleting model 'Turn'
        db.delete_table(u'diplomacy_turn')

        # Deleting model 'Power'
        db.delete_table(u'diplomacy_power')

        # Deleting model 'Territory'
        db.delete_table(u'diplomacy_territory')

        # Deleting model 'Subregion'
        db.delete_table(u'diplomacy_subregion')

        # Removing M2M table for field borders on 'Subregion'
        db.delete_table(db.shorten_name(u'diplomacy_subregion_borders'))

        # Deleting model 'Government'
        db.delete_table(u'diplomacy_government')

        # Deleting model 'Ownership'
        db.delete_table(u'diplomacy_ownership')

        # Deleting model 'Unit'
        db.delete_table(u'diplomacy_unit')

        # Deleting model 'OrderPost'
        db.delete_table(u'diplomacy_orderpost')

        # Deleting model 'Order'
        db.delete_table(u'diplomacy_order')

        # Deleting model 'CanonicalOrder'
        db.delete_table(u'diplomacy_canonicalorder')


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
            'assist': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'canonical_assist'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'canonical_target'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'diplomacy.order': {
            'Meta': {'object_name': 'Order'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'acts'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            'assist': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assisted'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': u"orm['diplomacy.OrderPost']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'targeted'", 'null': 'True', 'to': u"orm['diplomacy.Subregion']"}),
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
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Government']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'previous': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Unit']", 'null': 'True', 'blank': 'True'}),
            'standoff_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'standoff'", 'null': 'True', 'to': u"orm['diplomacy.Territory']"}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Subregion']"}),
            'turn': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['diplomacy.Turn']"}),
            'u_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['diplomacy']