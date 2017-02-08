from collections import defaultdict
from functools import partial
from random import shuffle

from django.contrib.auth.models import User
from django.db import models

from .engine import standard
from .engine.check import (valid_hold, valid_move, valid_support, valid_convoy,
                           valid_build, valid_disband)
from .engine.main import find_convoys, builds_available, generate, assist
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

def is_legal(order, units, owns, season):
    if isinstance(order, Order):
        order = {'government': order.post.government,
                 'turn': order.post.turn,
                 'actor': subregion_key(order.actor),
                 'action': order.action,
                 'assist': subregion_key(order.assist),
                 'target': subregion_key(order.target)}

    builds = builds_available(units, owns)

    if order['actor'] is None:
        if season != 'FA':
            return False
        unit = ()
    else:
        unit = [u for u in units if u['subregion'] == order['actor']]

    if order['actor'] is None or order['action'] is None:
        return (season == 'FA' and
                builds.get(order['government'].power.name, 0) > 0)
    if order['action'] != 'B' and not unit:
        return False

    if season in ('S', 'F'):
        if unit[0]['government'] != order['government'].power.name:
            return False
    elif season in ('SR', 'FR'):
        unit = [u for u in unit if u['dislodged']]
        if not unit:
            return False
        if unit[0]['government'] != order['government'].power.name:
            return False
    elif order['action'] == 'D':
        if unit and unit[0]['government'] != order['government'].power.name:
            return False
    elif order['action'] == 'B':
        if not any(o['territory'] == territory(order['actor'])
                   and o['government'] == order['government'].power.name
                   for o in owns):
            return False

    actions = {'H': valid_hold,
               'M': valid_move,
               'S': valid_support,
               'C': valid_convoy,
               'B': valid_build,
               'D': valid_disband}
    tree = actions[order['action']](order['actor'], units, owns, season)
    if not tree or order['assist'] not in tree:
        return False
    tree = tree[order['assist']]
    if order['target'] not in tree:
        return False
    return True

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
        owns = Ownership.objects.filter(turn=turn, territory__is_supply=True)
        units = Unit.objects.filter(turn=turn)
        orders = Order.objects.filter(post__turn=turn)
        return sorted(
            [(g, owns.filter(government=g).count(),
              units.filter(government=g).count(),
              bool(g.slots(turn)) == orders.filter(post__government=g).exists())
             for g in gvts],
            key=lambda x: (-x[1], -x[2], getattr(x[0].power, 'name', None)))

    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()

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

        orders = {
            territory(o['actor']): o
            for o in turn.normalize_orders()
            if o['actor'] is not None
        }

        units = turn.get_units()
        owns = turn.get_ownership()

        turn, orders, units, owns = generate(turn.as_data(), orders, units, owns)

        turn = self.turn_set.create(**turn)

        government_id = {
            gvt.power.name: gvt.id
            for gvt in self.government_set.select_related('power')
        }

        CanonicalOrder.objects.bulk_create([
            CanonicalOrder(**{
                'turn': turn.prev,
                'government_id': government_id[o['government']],
                'actor_id': subregion_id(o['actor']),
                'action': o['action'],
                'assist_id': subregion_id(o['assist']),
                'target_id': subregion_id(o['target']),
                'via_convoy': o['via_convoy'],
                'user_issued': o.get('user_issued', False),
            })
            for o in orders.itervalues()
        ])

        previous_id = {
            subregion_key(u.subregion): u.id
            for u in turn.prev.unit_set.select_related('subregion__territory')
        }

        Unit.objects.bulk_create([
            Unit(**{
                'turn': turn,
                'government_id': government_id[u['government']],
                'u_type': u['u_type'],
                'subregion_id': subregion_id(u['subregion']),
                'previous_id': previous_id.get(u['previous']),
                'dislodged': u['dislodged'],
                'displaced_from_id': t_id(u['displaced_from']),
                'standoff_from_id': t_id(u['standoff_from']),
            })
            for u in units
        ])

        Ownership.objects.bulk_create([
            Ownership(turn=turn,
                      government_id=government_id[o['government']],
                      territory_id=t_id(o['territory']))
            for o in owns
        ])

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

    # FIXME refactor
    def normalize_orders(self, gvt=None):
        gvts = (gvt,) if gvt else self.game.government_set.all()
        units = self.get_units()
        owns = self.get_ownership()

        # Construct the set of default orders.  This set is exhaustive, no units
        # outside or number of builds in excess will be permitted.
        if self.season == 'FA':
            builds = builds_available(units, owns)
            orders = {
                (g.id, s): {'user_issued': False, 'government': g.power.name,
                            'actor': None, 'action': None,
                            'assist': None, 'target': None,
                            'via_convoy': False, 'convoy': False}
                for g in gvts
                for s in xrange(abs(builds.get(g.power.name, 0)))
            }
        else:
            action = 'H' if self.season in ('S', 'F') else None
            orders = {
                (g.id, a.id): {'user_issued': False, 'government': g.power.name,
                               'actor': subregion_key(a), 'action': action,
                               'assist': None, 'target': None,
                               'via_convoy': False, 'convoy': False}
                for g in gvts
                for a in g.actors(self)
            }

        # Find the most recent set of posted orders from each relevant government.
        most_recent = {}
        for g in gvts:
            try:
                most_recent[g] = self.posts.filter(government=g).order_by('-id')[:1].get()
            except OrderPost.DoesNotExist:
                pass

        # For orders that were explicitly given, replace the default order if
        # the given order is legal.  Illegal orders are dropped.
        for gvt, post in most_recent.iteritems():
            i = 0
            for o in post.orders.select_related('actor__territory',
                                                'assist__territory',
                                                'target__territory'):
                if is_legal(o, units, owns, self.season):
                    if self.season == 'FA':
                        index = i
                        i += 1
                    else:
                        index = o.actor_id

                    # Drop the order if it falls outside of the set of allowable
                    # acting units or build quantity.
                    if (gvt.id, index) not in orders:
                        continue

                    orders[(gvt.id, index)] = {
                        'user_issued': True, 'government': post.government.power.name,
                        'actor': subregion_key(o.actor), 'action': o.action,
                        'assist': subregion_key(o.assist),
                        'target': subregion_key(o.target),
                        'via_convoy': o.via_convoy, 'convoy': False,
                    }

        if self.season in ('S', 'F'):
            for (g, index), o in orders.iteritems():
                # This block concerns the convoyability of units, so if the unit
                # isn't moving or isn't an army, ignore it.
                if o['action'] != 'M':
                    continue

                # Find all of the convoy orders that match the current move,
                # both overall and specifically by this user's government.
                matching = [(g2, o2) for (g2, i2), o2 in orders.iteritems()
                            if o2['action'] == 'C' and
                            assist(territory(o['actor']), o,
                                   territory(o2['actor']), o2)]
                gvt_matching = [o2 for g2, o2 in matching if g2 == g]

                if o['target'] in borders(o['actor']):
                    # If the target territory is adjacent to the moving unit,
                    # only mark as convoying when the user's government issued
                    # the convoy order, or the movement is explicitly marked as
                    # 'via convoy'.
                    o['convoy'] = bool(gvt_matching or
                                       (o['via_convoy'] and matching))
                else:
                    # If the target isn't adjacent, the unit clearly couldn't
                    # make it there on its own, so convoying is implied.  Allow
                    # any specified supporting convoy orders.
                    o['convoy'] = bool(matching)

        return [v for k, v in sorted(orders.iteritems())]


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

    def actors(self, turn=None):
        if not turn:
            turn = self.game.current_turn()
        if turn is None:
            return Subregion.objects.none()

        builds = builds_available(turn.get_units(), turn.get_ownership())

        if turn.season == 'FA' and builds.get(self.power.name, 0) > 0:
            actors = Subregion.objects.filter(
                territory__is_supply=True,
                territory__power__government=self, # home supply center
                territory__ownership__turn=turn,      # and it must still be
                territory__ownership__government=self # owned by you this turn
                ).exclude(
                territory__subregion__unit__turn=turn # and must be unoccupied
                ).distinct()
        else:
            displaced = {}
            if turn.season in ('SR', 'FR'): # only dislodged units move
                displaced['unit__dislodged'] = True
            actors = Subregion.objects.filter(unit__turn=turn,
                                              unit__government=self,
                                              **displaced)

        return actors

    def slots(self, turn):
        builds = builds_available(turn.get_units(), turn.get_ownership())
        if getattr(turn, 'season', '') == 'FA':
            return abs(builds.get(self.power.name, 0))
        return self.actors(turn).count()

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
        for a in self.actors(turn):
            for x in actions[turn.season]:
                result = helper[x](subregion_key(a), units, owns, season)
                if not result:
                    continue
                tree.setdefault(a.id, {})[x] = {
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
