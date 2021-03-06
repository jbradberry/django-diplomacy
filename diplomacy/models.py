from collections import defaultdict
from functools import partial
from random import shuffle

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from .engine import standard
from .engine.check import (valid_hold, valid_move, valid_support, valid_convoy,
                           valid_build, valid_disband)
from .engine.digest import builds_available, actionable_subregions
from .engine.main import generate, initialize_game
from .engine.utils import is_supply, unit_display, subregion_display


convert = {'L': 'A', 'S': 'F'}

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


class DiplomacyPrefs(models.Model):
    class Meta:
        verbose_name_plural = "diplomacyprefs"

    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
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
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="diplomacy_games")
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    open_joins = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('diplomacy_game_detail', kwargs={'slug': self.slug})

    def governments(self, turn=None):
        gvts = self.government_set.all()
        units, owns, posts, actors = (), (), (), {}
        if turn:
            units = turn.get_units()
            owns = turn.get_ownership()
            posts = turn.posts.select_related('government')
            actors = actionable_subregions(turn.as_data(), units, owns)

        return sorted(
            ((g,
              sum(1 for o in owns
                  if o['government'] == g.power
                  and o['is_supply']),
              sum(1 for u in units if u['government'] == g.power),
              any(post.government == g for post in posts) or not actors.get(g.power))
             for g in gvts),
            key=lambda x: (-x[1], -x[2], getattr(x[0].power, 'name', None))
        )

    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()

    def create_turn(self, turn_data):
        return self.turn_set.create(**turn_data)

    def activate(self):
        if self.state != 'S' or self.turn_set.exists():
            return False
        if self.government_set.count() != 7:
            return False

        governments = list(self.government_set.all())
        shuffle(governments)
        for pwr, gvt in zip(standard.powers, governments):
            gvt.power = pwr
            gvt.save()

        turn, units, owns = initialize_game()

        turn = self.create_turn(turn)
        turn.create_units(units)
        turn.create_ownership(owns)

        self.state = 'A'
        self.save()
        return True

    activate.alters_data = True

    def generate(self):
        turn = self.current_turn()
        orders = turn.get_orders()
        units = turn.get_units()
        owns = turn.get_ownership()

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

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    number = models.IntegerField()
    year = models.IntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "{0} {1}".format(self.get_season_display(), self.year)

    def get_absolute_url(self):
        return reverse(
            'diplomacy_turn_detail',
            kwargs={
                'slug': self.game.slug,
                'season': self.season,
                'year': str(self.year),
            }
        )

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
                gvt.power: gvt.id
                for gvt in self.game.government_set.all()
            }

        return self._government_lookup

    def create_canonical_orders(self, orders):
        CanonicalOrder.objects.bulk_create([
            CanonicalOrder(**{
                'turn': self.prev,
                'government_id': self.government_lookup[o['government']],
                'actor': o['actor'],
                'action': o['action'],
                'assist': o.get('assist', ''),
                'target': o.get('target', ''),
                'via_convoy': o['via_convoy'],
                'user_issued': o.get('user_issued', False),
                'result': o['result'],
            })
            for o in orders
        ])

    def create_units(self, units):
        Unit.objects.bulk_create([
            Unit(**{
                'turn': self,
                'government_id': self.government_lookup[u['government']],
                'u_type': u['u_type'],
                'subregion': u['subregion'],
                'previous': u.get('previous', ''),
                'dislodged': u.get('dislodged', False),
                'displaced_from': u.get('displaced_from', ''),
                'standoff_from': u.get('standoff_from', ''),
            })
            for u in units
        ])

    def create_ownership(self, owns):
        Ownership.objects.bulk_create([
            Ownership(turn=self,
                      government_id=self.government_lookup[o['government']],
                      territory=o['territory'])
            for o in owns
        ])

    def get_units(self):
        return [
            {'government': u.government.power,
             'u_type': u.u_type,
             'subregion': u.subregion,
             'previous': u.previous,
             'dislodged': u.dislodged,
             'displaced_from': u.displaced_from,
             'standoff_from': u.standoff_from}
            for u in self.unit_set.select_related('government')
        ]

    def get_ownership(self):
        return [
            {'territory': o.territory,
             'government': o.government.power,
             'is_supply': is_supply(o.territory)}
            for o in self.ownership_set.select_related('government')
        ]

    def get_orders(self):
        posts = {}
        for p in self.posts.prefetch_related('orders'):
            posts[p.government_id] = p

        return [o.as_data() for p in posts.values()
                for o in p.orders.all()]

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
        ).prefetch_related(
            'unit_set', 'canonicalorder_set__government'
        ).order_by('number')

        units_index = {
            (t.number, u.government_id, u.subregion): u.previous
            for t in list(turns)[1:]
            for u in t.unit_set.all()
            if u.previous
        }

        # dict of dicts of lists; keys=power, original unit id
        orders = defaultdict(partial(defaultdict, list))

        for t in turns:
            for o in t.canonicalorder_set.all():
                power = o.government.power_display
                if o.action == 'B':
                    actor = 'b.{0}'.format(o.actor)
                else:
                    N, G, actor = t.number, o.government_id, o.actor
                    while (N, G, actor) in units_index:
                        actor = units_index[(N, G, actor)]
                        N -= 1

                orders[power][actor].append(o)

        return sorted((power, sorted(adict.items()))
                      for power, adict in orders.items())


class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    power = models.CharField(max_length=32, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def power_display(self):
        return standard.powers.get(self.power, u'')

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
                   'FA': ('B',) if builds.get(self.power, 0) > 0 else ('D',)}
        helper = {'H': valid_hold,
                  'M': valid_move,
                  'S': valid_support,
                  'C': valid_convoy,
                  'B': valid_build,
                  'D': valid_disband}

        tree = {}
        for a in actionable_subregions(turn.as_data(), units, owns).get(self.power, ()):
            for x in actions[turn.season]:
                result = helper[x](a, units, owns, season)
                if not result:
                    continue
                tree.setdefault(a, {})[x] = {
                    (assist or u''): {
                        target or u'': v
                        for target, v in targets.items()
                    }
                    for assist, targets in result.items()
                }

        if season == 'FA' and builds.get(self.power, 0) > 0:
            tree[u''] = {u'': {u'': {u'': False}}}

        return tree


class Ownership(models.Model):
    class Meta:
        unique_together = ('turn', 'territory')

    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    government = models.ForeignKey(Government, on_delete=models.CASCADE)
    territory = models.CharField(max_length=32, blank=True)


class Unit(models.Model):
    class Meta:
        ordering = ('-turn', 'government', 'subregion')

    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    government = models.ForeignKey(Government, on_delete=models.CASCADE)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.CharField(max_length=64, blank=True)
    previous = models.CharField(max_length=64, blank=True)
    dislodged = models.BooleanField(default=False)
    displaced_from = models.CharField(max_length=32, blank=True)
    standoff_from = models.CharField(max_length=32, blank=True)

    def __unicode__(self):
        return unit_display(self.subregion)


class OrderPost(models.Model):
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='posts')
    government = models.ForeignKey(Government, on_delete=models.CASCADE, related_name='posts')
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
    post = models.ForeignKey(OrderPost, on_delete=models.CASCADE, related_name='orders')

    actor = models.CharField(max_length=64, blank=True)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES,
                              null=True, blank=True)
    assist = models.CharField(max_length=64, blank=True)
    target = models.CharField(max_length=64, blank=True)
    via_convoy = models.BooleanField(default=False)

    def __unicode__(self):
        result = u"{actor} {action}".format(actor=unit_display(self.actor),
                                            action=self.action)
        if self.assist:
            result = u"{order} {assist}".format(order=result,
                                                assist=unit_display(self.assist))
        if self.target:
            result = u"{order} {target}".format(order=result,
                                                target=subregion_display(self.target))
        if self.via_convoy:
            result = u"{order} via Convoy".format(order=result)
        return result

    def as_data(self):
        return {
            'government': self.post.government.power,
            'actor': self.actor,
            'action': self.action,
            'assist': self.assist,
            'target': self.target,
            'via_convoy': self.via_convoy,
        }


class CanonicalOrder(models.Model):
    RESULT_CHOICES = (
        ('S', 'Succeeded'),
        ('F', 'Failed'),
        ('B', 'Bounced'),
        ('D', 'Destroyed'),
    )

    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    government = models.ForeignKey(Government, on_delete=models.CASCADE)

    actor = models.CharField(max_length=64, blank=True)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES,
                              null=True, blank=True)
    assist = models.CharField(max_length=64, blank=True)
    target = models.CharField(max_length=64, blank=True)
    via_convoy = models.BooleanField(default=False)

    user_issued = models.BooleanField(default=True)
    result = models.CharField(max_length=1, choices=RESULT_CHOICES)

    def __unicode__(self):
        order = u"{actor} {action}".format(actor=unit_display(self.actor),
                                           action=self.action)
        if self.assist:
            order = u"{order} {assist}".format(order=order,
                                               assist=unit_display(self.assist))
        if self.target:
            order = u"{order} {target}".format(order=order,
                                               target=subregion_display(self.target))
        if self.via_convoy:
            order = u"{order} via Convoy".format(order=order)
        return u"{order} [{result}]".format(order=order, result=self.get_result_display())

    @property
    def full_actor(self):
        return unit_display(self.actor)

    @property
    def full_assist(self):
        return unit_display(self.assist)

    @property
    def full_target(self):
        return subregion_display(self.target)
