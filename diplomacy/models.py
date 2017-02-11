from collections import defaultdict
from functools import partial
from random import shuffle

from django.contrib.auth.models import User
from django.db import models

from .engine import standard
from .engine.check import (valid_hold, valid_move, valid_support, valid_convoy,
                           valid_build, valid_disband, is_legal)
from .engine.compare import assist
from .engine.main import (find_convoys, builds_available, actionable_subregions,
                          normalize_orders, generate)
from .engine.utils import territory, borders, territory_parts
from .helpers import unit, convert


SEASON_CHOICES = (
    ('S', 'Spring'),
    ('SR', 'Spring Retreat'),
    ('F', 'Fall'),
    ('FR', 'Fall Retreat'),
    ('FA', 'Fall Adjustment')
)

UNIT_CHOICES = (
    ('A', 'Army'),
    ('F', 'Fleet')
)

SUBREGION_CHOICES = (
    ('L', 'Land'),
    ('S', 'Sea')
)


# Refactor wrapper functions

def t_key_closure():
    lookup_table = {}

    def t_key(t_id):
        if not lookup_table:
            lookup_table.update((t.id, t.name) for t in Territory.objects.all())

        return lookup_table[t_id]

    return t_key

t_key = t_key_closure()

def t_id_closure():
    lookup_table = {}

    def t_id(t_key):
        if not lookup_table:
            lookup_table.update((t.name, t.id) for t in Territory.objects.all())

        return lookup_table.get(t_key)

    return t_id

t_id = t_id_closure()

def subregion_id_closure():
    lookup_table = {}

    def subregion_id(sr_key):
        if not lookup_table:
            lookup_table.update((subregion_key(sr), sr.id)
                                for sr in Subregion.objects.select_related('territory'))

        return lookup_table.get(sr_key)

    return subregion_id

subregion_id = subregion_id_closure()

def subregion_obj_closure():
    lookup_table = {}

    def subregion_obj(sr_key):
        if not lookup_table:
            lookup_table.update((subregion_key(sr), sr)
                                for sr in Subregion.objects.select_related('territory'))

            return lookup_table.get(sr_key)

    return subregion_obj

subregion_obj = subregion_obj_closure()

# End of refactor wrapper functions

def subregion_key(sr):
    if not sr:
        return None
    return (sr.territory.name, sr.subname, sr.sr_type)


class DiplomacyPrefs(models.Model):
    class Meta:
        verbose_name_plural = "diplomacyprefs"

    user = models.OneToOneField("auth.User")
    warnings = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.user)


class Game(models.Model):
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name="diplomacy_games")
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    open_joins = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy_game_detail', (), {'slug': self.slug})

    def governments(self, turn=None):
        gvts = self.government_set.all()
        units, owns, posts = (), (), ()
        if turn:
            units = turn.get_units()
            owns = turn.get_ownership()
            posts = turn.posts.select_related('government')

        return sorted(
            ((g,
              sum(1 for o in owns
                  if o['government'] == g.power.name
                  and o['is_supply']),
              sum(1 for u in units if u['government'] == g.power.name),
              any(post.government == g for post in posts))
             for g in gvts),
            key=lambda x: (-x[1], -x[2], getattr(x[0].power, 'name', None))
        )

    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()

    def create_turn(self, turn_data):
        return self.turn_set.create(**turn_data)

    # FIXME refactor
    def activate(self):
        if self.state != 'S' or self.turn_set.exists():
            return False
        if self.government_set.count() != 7:
            return False
        turn = self.turn_set.create(number=0, year=1900, season='S')
        governments = list(self.government_set.all())
        shuffle(governments)
        for pwr, gvt in zip(Power.objects.all(), governments):
            gvt.power = pwr
            gvt.save()
            for t in Territory.objects.filter(power=pwr):
                Ownership(turn=turn, government=gvt, territory=t).save()

            sr_set = Subregion.objects.filter(territory__power=pwr,
                                              init_unit=True)
            for sr in sr_set:
                gvt.unit_set.create(turn=turn,
                                    u_type=convert[sr.sr_type],
                                    subregion=sr)
        self.state = 'A'
        self.save()
        return True

    activate.alters_data = True

    def generate(self):
        turn = self.current_turn()
        orders = turn.get_orders()
        units = turn.get_units()
        owns = turn.get_ownership()

        orders = {
            territory(o['actor']): o
            for o in normalize_orders(turn.as_data(), orders, units, owns)
            if o['actor'] is not None
        }

        turn, orders, units, owns = generate(turn.as_data(), orders, units, owns)

        turn = self.create_turn(turn)
        turn.create_canonical_orders(orders)
        turn.create_units(units)
        turn.create_ownership(owns)

        return True

    generate.alters_data = True


class Turn(models.Model):
    class Meta:
        get_latest_by = 'generated'
        ordering = ('-generated',)

    game = models.ForeignKey(Game)
    number = models.IntegerField()
    year = models.IntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "{0} {1}".format(self.get_season_display(), self.year)

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy_turn_detail', (), {
            'slug': self.game.slug,
            'season': self.season,
            'year': str(self.year),})

    def as_data(self):
        return {
            'number': self.number,
            'year': self.year,
            'season': self.season,
        }

    @property
    def prev(self):
        if getattr(self, '_prev', None):
            return self._prev

        earlier = self.game.turn_set.filter(number=self.number - 1)
        if earlier:
            self._prev = earlier.get()
            return self._prev

    @property
    def next(self):
        if getattr(self, '_next', None):
            return self._next

        later = self.game.turn_set.filter(number=self.number + 1)
        if later:
            self._next = later.get()
            return self._next

    @property
    def government_lookup(self):
        if not getattr(self, '_government_lookup', None):
            self._government_lookup = {
                gvt.power.name: gvt.id
                for gvt in self.game.government_set.select_related('power')
            }

        return self._government_lookup

    def create_canonical_orders(self, orders_index):
        CanonicalOrder.objects.bulk_create([
            CanonicalOrder(**{
                'turn': self.prev,
                'government_id': self.government_lookup[o['government']],
                'actor_id': subregion_id(o['actor']),
                'action': o['action'],
                'assist_id': subregion_id(o['assist']),
                'target_id': subregion_id(o['target']),
                'via_convoy': o['via_convoy'],
                'user_issued': o.get('user_issued', False),
            })
            for o in orders_index.itervalues()
        ])

    def create_units(self, units):
        previous_id = {
            subregion_key(u.subregion): u.id
            for u in self.prev.unit_set.select_related('subregion__territory')
        }

        Unit.objects.bulk_create([
            Unit(**{
                'turn': self,
                'government_id': self.government_lookup[u['government']],
                'u_type': u['u_type'],
                'subregion_id': subregion_id(u['subregion']),
                'previous_id': previous_id.get(u['previous']),
                'dislodged': u['dislodged'],
                'displaced_from_id': t_id(u['displaced_from']),
                'standoff_from_id': t_id(u['standoff_from']),
            })
            for u in units
        ])

    def create_ownership(self, owns):
        Ownership.objects.bulk_create([
            Ownership(turn=self,
                      government_id=self.government_lookup[o['government']],
                      territory_id=t_id(o['territory']))
            for o in owns
        ])

    def get_units(self):
        return [
            {'government': u.government.power.name,
             'u_type': u.u_type,
             'subregion': subregion_key(u.subregion),
             'previous': subregion_key(getattr(u.previous, 'subregion', None)),
             'dislodged': u.dislodged,
             'displaced_from': getattr(u.displaced_from, 'name', ''),
             'standoff_from': getattr(u.standoff_from, 'name', '')}
            for u in self.unit_set.select_related('subregion__territory',
                                                  'previous__subregion__territory',
                                                  'displaced_from',
                                                  'standoff_from',
                                                  'government__power')
        ]

    def get_ownership(self):
        return [
            {'territory': o.territory.name,
             'government': o.government.power.name,
             'is_supply': o.territory.is_supply}
            for o in self.ownership_set.select_related('territory', 'government__power')
        ]

    def get_orders(self):
        posts = {}
        for p in self.posts.prefetch_related('orders__actor__territory',
                                             'orders__assist__territory',
                                             'orders__target__territory'):
            posts[p.government_id] = p

        return [o.as_data() for p in posts.itervalues()
                for o in p.orders.all()]

    # FIXME refactor
    def recent_orders(self):
        seasons = {'S': ['F', 'FR', 'FA'],
                   'SR': ['S'],
                   'F': ['S', 'SR'],
                   'FR': ['F'],
                   'FA': ['F', 'FR']}
        turns = self.game.turn_set.filter(
            season__in=seasons[self.season],
            number__gt=self.number - 5,
            number__lt=self.number
        ).select_related('unit', 'canonical_order').order_by('number')

        units = {}
        for t in turns:
            units.update((u.id, getattr(u.previous, 'id', None))
                          for u in t.unit_set.all())

        # dict of dicts of lists; keys=power, original unit id
        orders = defaultdict(partial(defaultdict, list))

        for t in turns:
            for o in t.canonicalorder_set.select_related('government__power'):
                p = unicode(o.government.power)
                u = t.unit_set.filter(government=o.government,
                                      subregion=o.actor)
                u = u.get() if u else None
                if u is None:
                    orders[p]["b{0}".format(o.actor_id)].append(o)
                    continue
                u_id = u.id
                while u_id in units:
                    n = u_id
                    u_id = units[u_id]
                orders[p][n].append(o)

        return sorted((power, sorted(adict.iteritems()))
                      for power, adict in orders.iteritems())


class Power(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Territory(models.Model):
    name = models.CharField(max_length=30)
    power = models.ForeignKey(Power, null=True, blank=True)
    is_supply = models.BooleanField()

    def __unicode__(self):
        return self.name


class Subregion(models.Model):
    class Meta:
        ordering = ('id',)

    territory = models.ForeignKey(Territory)
    subname = models.CharField(max_length=10, blank=True)
    sr_type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    init_unit = models.BooleanField()
    borders = models.ManyToManyField("self", null=True, blank=True)

    def __unicode__(self):
        if self.subname:
            return u'{0} ({1})'.format(self.territory.name, self.subname)
        else:
            return self.territory.name


class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power, null=True, blank=True)
    owns = models.ManyToManyField(Territory, through='Ownership')

    def __unicode__(self):
        return self.name

    def filter_orders(self):
        turn = self.game.current_turn()
        season = turn.season
        units = turn.get_units()
        owns = turn.get_ownership()
        builds = builds_available(units, owns)

        actions = {'S': ('H', 'M', 'S', 'C'),
                   'F': ('H', 'M', 'S', 'C'),
                   'SR': ('M', 'D'),
                   'FR': ('M', 'D'),
                   'FA': ('B',) if builds.get(self.power.name, 0) > 0 else ('D',)}
        helper = {'H': valid_hold,
                  'M': valid_move,
                  'S': valid_support,
                  'C': valid_convoy,
                  'B': valid_build,
                  'D': valid_disband}

        tree = {}
        for a in actionable_subregions(turn.as_data(), units, owns).get(self.power.name, ()):
            for x in actions[turn.season]:
                result = helper[x](a, units, owns, season)
                if not result:
                    continue
                tree.setdefault(subregion_id(a), {})[x] = {
                    (subregion_id(assist) or u''): {
                        subregion_id(target) or u'': v
                        for target, v in targets.iteritems()
                    }
                    for assist, targets in result.iteritems()
                }

        if season == 'FA' and builds.get(self.power.name, 0) > 0:
            tree[u''] = {u'': {u'': {u'': False}}}

        return tree


class Ownership(models.Model):
    class Meta:
        unique_together = ("turn", "territory")

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    territory = models.ForeignKey(Territory)


class Unit(models.Model):
    class Meta:
        ordering = ('-turn', 'government', 'subregion')

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)
    previous = models.ForeignKey("self", null=True, blank=True)
    dislodged = models.BooleanField(default=False)
    displaced_from = models.ForeignKey(Territory, null=True, blank=True,
                                       related_name='displaced')
    standoff_from = models.ForeignKey(Territory, null=True, blank=True,
                                      related_name='standoff')

    def __unicode__(self):
        return u'{0} {1}'.format(self.u_type, self.subregion.territory)


class OrderPost(models.Model):
    turn = models.ForeignKey(Turn, related_name='posts')
    government = models.ForeignKey(Government, related_name='posts')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',)
        get_latest_by = 'timestamp'


ACTION_CHOICES = (
    ('H', 'Hold'),
    ('M', 'Move'),
    ('S', 'Support'),
    ('C', 'Convoy'),
    ('B', 'Build'),
    ('D', 'Disband')
)


class Order(models.Model):
    post = models.ForeignKey(OrderPost, related_name='orders')

    actor = models.ForeignKey(Subregion, null=True, blank=True,
                              related_name='acts')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES,
                              null=True, blank=True)
    assist = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='assisted')
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='targeted')
    via_convoy = models.BooleanField()

    def __unicode__(self):
        result = u"{0} {1} {2}".format(
            convert.get(getattr(self.actor, 'sr_type', None)),
            self.actor, self.action)
        if self.assist:
            result = u"{0} {1} {2}".format(result,
                                           convert[self.assist.sr_type],
                                           self.assist)
        if self.target:
            result = u"{0} {1}".format(result, self.target)
        if self.via_convoy:
            result = u"{0} via Convoy".format(result)
        return result

    def as_data(self):
        return {
            'government': self.post.government.power.name,
            'actor': subregion_key(self.actor),
            'action': self.action,
            'assist': subregion_key(self.assist),
            'target': subregion_key(self.target),
            'via_convoy': self.via_convoy,
        }


class CanonicalOrder(models.Model):
    RESULT_CHOICES = (
        ('S', 'Succeeded'),
        ('F', 'Failed'),
        ('B', 'Bounced'),
        ('D', 'Destroyed'),
    )

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)

    actor = models.ForeignKey(Subregion, related_name='canonical_actor')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES,
                              null=True, blank=True)
    assist = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='canonical_assist')
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='canonical_target')
    via_convoy = models.BooleanField()

    user_issued = models.BooleanField()
    result = models.CharField(max_length=1, choices=RESULT_CHOICES)

    @property
    def full_actor(self):
        return unit(self.actor)

    @property
    def full_assist(self):
        if self.assist:
            return unit(self.assist)
