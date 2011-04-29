from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from random import shuffle
from itertools import permutations
import datetime

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


def assist(a1, o1, a2, o2):
    return o2['assist'] == a1

def attack_us(a1, o1, a2, o2):
    return o2['target'] == a1

def head_to_head(a1, o1, a2, o2):
    return o2['target'] == a1 and o1['target'] == a2

def hostile_assist_hold(a1, o1, a2, o2):
    return o2['assist'] == o1['target'] and o2['target'] is None

def hostile_assist_compete(a1, o1, a2, o2):
    return o2['target'] == o1['target']

def move_away(a1, o1, a2, o2):
    return o1['target'] == a2 # and o2['target'] != a1 ?


DEPENDENCIES = {('C', 'M'): (attack_us,),
                ('S', 'C'): (attack_us,),
                ('H', 'S'): (assist, attack_us),
                ('M', 'S'): (assist, hostile_assist_compete,
                             head_to_head, hostile_assist_hold),
                ('M', 'C'): (assist,),
                ('M', 'M'): (move_away,),}


class Game(models.Model):
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    requests = models.ManyToManyField(User, related_name='requests')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy.views.games_detail', (), {
            'slug': self.slug})

    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()
        else:
            return None

    def detect_civil_disorder(self, orders):
        return [gvt for gvt in self.government_set.all()
                if not any('id' in o for u, o in orders.iteritems()
                           if o['government'] == gvt)]

    def construct_dependencies(self, orders):
        dep = {}
        for (a1, o1), (a2, o2) in permutations(orders.iteritems(), 2):
            depend = False
            act1, act2 = o1['action'], o2['action']
            if (act1, act2) in DEPENDENCIES:
                depend = any(f(a1, o1, a2, o2) for f in
                             DEPENDENCIES[(act1, act2)])

            if depend:
                dep.setdefault(a1, []).append(a2)

        return dep

    def immediate_fails(self, orders):
        results = ()
        for a, o in orders.iteritems():
            if o['action'] not in ('S', 'C'):
                continue
            assist = orders[o['assist']]
            if o['target'] is not None:
                if assist['action'] == 'M' and assist['target'] == o['target']:
                    continue
            else:
                if assist['action'] in ('H', 'C', 'S'):
                    continue
            results = results + ((a, False),)

        return results

    # FIXME
    def _resolve(self, order, orders, dep):
        pass

    # FIXME
    def consistent(self, state):
        pass

    def resolve(self, state, orders, dep):
        _state = set(o for o, d in state)

        # Any orders that have no more unresolved dependencies should
        # be brought into our new hypothetical order resolution.
        new_state = tuple((order, self._resolve(order, orders, dep))
                          for order in orders
                          if order not in _state and
                          all(o in _state for o in dep[order]))
        state = state + new_state
        _state |= set(o for o, d in new_state)

        # Only bother calculating whether the hypothetical solution is
        # consistent if all orders within it have no remaining
        # unresolved dependencies.
        if all(all(o in _state for o in dep[order]) for order in state):
            if not self.consistent(state):
                return ()

        # For those orders not already in 'state', sort from least to
        # most remaining dependencies.
        remaining_deps = sorted((sum(1 for o in dep[order]
                                     if o not in _state), order)
                                for order in orders if order not in _state)
        if not remaining_deps:
            return state
        # Go with the order with the fewest remaining deps.
        q, order = remaining_deps[0]

        # The order has unresolved deps which might be circular, so it
        # isn't obvious how to resolve it.  Try both ways.
        results = []
        for S in (True, False):
            results.append(self.resolve(state+((order, S),), orders, dep))

        # FIXME: detect and handle convoy paradoxes
        return results[0] if results[0] else results[1]

    def generate(self):
        turn = self.current_turn()

        turn.consistency_check()

        orders = dict((o['actor'].id, o) for o in turn.canonical_orders())
        if turn.season in ('S', 'F'):
            # FIXME: do something with civil disorder
            disorder = self.detect_civil_disorder(orders)
            dependencies = self.construct_dependencies(orders)
            state = self.immediate_fails(orders)
            decisions = self.resolve(state, orders, dependencies)

        turn = self.turn_set.create(number=turn.number+1)
        turn.update_units(decisions)
        turn.update_ownership()

        turn.consistency_check()

    generate.alters_data = True


def game_changed(sender, **kwargs):
    instance = kwargs['instance']
    if instance.state == 'A' and not instance.turn_set.exists():
        turn = instance.turn_set.create(number=0)
        convert = {'L': 'A', 'S': 'F'}
        governments = list(instance.government_set.all())
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
post_save.connect(game_changed, sender=Game)


class Turn(models.Model):
    class Meta:
        get_latest_by = 'generated'
        ordering = ['-generated']

    game = models.ForeignKey(Game)
    number = models.IntegerField()
    year = models.IntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.get_season_display(), self.year)

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy.views.turns_detail', (), {
            'game': self.game.slug,
            'turn': '%s%s' % (self.season, self.year)})

    def governments(self):
        gvts = Government.objects.filter(game=self.game)
        owns = Ownership.objects.filter(turn=self, territory__is_supply=True)
        return sorted([(g, sum(1 for t in owns if t.government.id == g.id))
                       for g in gvts], key=lambda x: (-x[1], x[0].power.name))

    def find_convoys(self):
        """
        Generates pairs consisting of a cluster of adjacent non-coastal
        fleets, and the coastal territories that are reachable via convoy
        from that cluster.  This is necessary to determine legal orders.

        """
        if hasattr(self, '_convoyable'):
            return self._convoyable

        fleets = Subregion.objects.filter(
            sr_type='S', unit__turn=self).exclude(
            territory__subregion__sr_type='L').distinct()
        C = dict((f.id, set([f.id])) for f in fleets)
        for f in fleets:
            for f2 in fleets.filter(borders=f):
                if C[f.id] is not C[f2.id]:
                    C[f.id] |= C[f2.id]
                    C.update((x, C[f.id]) for x in C[f2.id])
        groups = set(frozenset(C[f]) for f in C)
        self._convoyable = []
        for g in groups:
            coasts = Subregion.objects.filter(
                sr_type='L', territory__subregion__borders__id__in=g
                ).distinct()
            if coasts.filter(unit__turn=self).exists():
                self._convoyable.append((g, set(sr.id for sr in coasts)))
        return self._convoyable

    def valid_hold(self, actor, empty=None):
        if self.season in ('S', 'F'):
            if self.unit_set.filter(subregion=actor).count() == 1:
                return {empty: [empty]}
        return {}

    def valid_move(self, actor, empty=None):
        if self.season == 'FA':
            return {}

        unit = self.unit_set.filter(subregion=actor)
        target = Subregion.objects.filter(borders=actor)

        if self.season in ('SR', 'FR'):
            # only displaced units retreat
            unit = unit.filter(displaced_from__isnull=False)
            target = target.exclude(
                # only go to empty territories ...
                territory__subregion__unit__turn=self).exclude(
                # that we weren't displaced from ...
                territory=unit.displaced_from).exclude(
                # and that isn't empty because of a standoff.
                territory__standoff__turn=self).distinct()

        if unit.count() != 1:
            return {}
        target = [t.id for t in target]

        if self.season in ('S', 'F') and unit.get().u_type == 'A':
            target = set(target)
            for fset, lset in self.find_convoys():
                if actor.id in lset:
                    target.update(lset)
            target.discard(actor.id)
            target = list(target)

        if not target:
            return {}
        return {empty: target}

    def valid_support(self, actor, empty=None):
        if self.season not in ('S', 'F'):
            return {}
        if self.unit_set.filter(subregion=actor).count() != 1:
            return {}

        sr = Subregion.objects.all()
        adj = sr.filter(territory__subregion__borders=actor).distinct()

        # support to hold
        results = dict((a.id, [empty]) for a in adj.filter(unit__turn=self))

        adj = set(a.id for a in adj)

        # support to attack
        attackers = sr.filter(territory__subregion__borders__borders=actor,
                              unit__turn=self
                              ).exclude(id=actor.id).distinct()
        for a in attackers:
            reachable = adj & set(t.id for t in a.borders.all())
            results.setdefault(a.id, []).extend(reachable)

        # support to convoyed attack
        attackers = sr.filter(unit__turn=self, sr_type='L'
                              ).exclude(id=actor.id).distinct()
        for fset, lset in self.find_convoys():
            for a in attackers:
                if a.id not in lset:
                    continue
                results.setdefault(a.id, []).extend(adj & lset - set([a.id]))

        return results

    def valid_convoy(self, actor, empty=None):
        if self.season not in ('S', 'F'):
            return {}
        if self.unit_set.filter(subregion=actor).count() != 1:
            return {}
        if actor.sr_type != 'S':
            return {}

        sr = Subregion.objects.all()
        for fset, lset in self.find_convoys():
            if actor in fset:
                attackers = sr.filter(unit__turn=self, sr_type='L',
                                      id__in=lset).distinct()
                return dict((a.id, list(lset - set([a.id]))) for a in attackers)
        return {}

    def valid_build(self, actor, empty=None):
        if not self.season == 'FA':
            return {}
        T = actor.territory
        G = T.ownership_set.get(turn=self)
        if not (T.is_supply and G.builds_available() > 0):
            return {}
        if T.subregion_set.filter(unit__turn=self).exists():
            return {}
        if T.ownership_set.filter(turn=self,
                                  government__power=T.power).exists():
            return {empty: [empty]}
        return {}

    def valid_disband(self, actor, empty=None):
        if self.season in ('S', 'F'):
            return {}

        unit = actor.unit_set.filter(turn=self)
        if self.season in ('SR', 'FR'):
            if not unit.filter(displaced_from__is_null=False).exists():
                return {}
        elif unit.get().government.builds_available() >= 0:
            return {}
        return {empty: [empty]}

    # FIXME
    def consistency_check(self):
        pass

    # FIXME
    def is_legal(self, order):
        return True

    def canonical_orders(self, gvt=None):
        gvts = (gvt,) if gvt else self.game.government_set.all()

        # fallback orders
        if self.season == 'FA':
            orders = dict(((g, s), {'government': g, 'slot': s, 'turn': self})
                          for g in gvts for s in abs(g.builds_available()))
        else:
            action = 'H' if self.season in ('S', 'F') else None
            orders = dict(((g, s),
                           {'government': g, 'slot': s, 'turn': self,
                            'actor': a, 'action': action})
                          for g in gvts for s, a in enumerate(g.actors(self)))

        # use the most recent legal order
        orderset = self.order_set.all()
        if gvt:
            orderset = orderset.filter(government=gvt)
        for o in orderset:
            if self.is_legal(o):
                orders[(o.government, o.slot)] = {
                    'id': o.id, 'government': o.government, 'slot': o.slot,
                    'turn': o.turn, 'actor': o.actor, 'action': o.action,
                    'assist': o.assist, 'target': o.target}
        return [v for k, v in sorted(orders.iteritems())]

    # FIXME
    def update_units(self, decisions):
        pass

    def update_ownership(self):
        prev = Turn.objects.get(number=self.number-1)
        for t in Territory.objects.all():
            u = self.unit_set.filter(subregion__territory=t)

            try:
                if self.season == 'F' and u.exists():
                    gvt = u[0].government
                else:
                    gvt = prev.ownership_set.get(territory=t).government
            except ObjectDoesNotExist:
                continue

            self.ownership_set.create(government=gvt, territory=t)


def turn_create(sender, **kwargs):
    instance = kwargs['instance']
    if instance.id: return
    instance.year = 1900 + instance.number // len(SEASON_CHOICES)
    instance.season = SEASON_CHOICES[instance.number % len(SEASON_CHOICES)][0]
pre_save.connect(turn_create, sender=Turn)


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
        ordering = ['id']

    territory = models.ForeignKey(Territory)
    subname = models.CharField(max_length=10, blank=True)
    sr_type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    init_unit = models.BooleanField()
    borders = models.ManyToManyField("self", null=True, blank=True)

    def __unicode__(self):
        if self.subname:
            return u'%s (%s)' % (self.territory.name, self.subname)
        else:
            return self.territory.name


class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power, null=True)
    owns = models.ManyToManyField(Territory, through='Ownership')

    def __unicode__(self):
        return self.name

    def supplycenters(self, turn=None):
        if not turn:
            turn = self.game.current_turn()
        return self.owns.filter(ownership__turn=turn,
                                is_supply=True).count()

    def units(self, turn=None):
        if not turn:
            turn = self.game.current_turn()
        return Unit.objects.filter(turn=turn, government=self).count()

    def builds_available(self):
        return self.supplycenters() - self.units()

    def actors(self, turn=None):
        if not turn:
            turn = self.game.current_turn()

        if turn.season == 'FA':
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
                displaced['unit__displaced_from__isnull'] = False
            actors = Subregion.objects.filter(unit__turn=turn,
                                              unit__government=self,
                                              **displaced)

        return actors

    def filter_orders(self):
        turn = self.game.current_turn()
        season = turn.season
        builds = self.builds_available()

        actions = {'S': ('H', 'M', 'S', 'C'),
                   'F': ('H', 'M', 'S', 'C'),
                   'SR': ('M', 'D'),
                   'FR': ('M', 'D'),
                   'FA': ('B',) if builds > 0 else ('D',)}
        helper = {'H': turn.valid_hold,
                  'M': turn.valid_move,
                  'S': turn.valid_support,
                  'C': turn.valid_convoy,
                  'B': turn.valid_build,
                  'D': turn.valid_disband}

        tree = {}
        for a in self.actors(turn):
            for x in actions[turn.season]:
                result = helper[x](a, u'')
                if not result:
                    continue
                tree.setdefault(a.id, {})[x] = result

        if season == 'FA' and builds > 0:
            tree[u''] = {u'': {u'': [u'']}}

        return tree


class Ownership(models.Model):
    class Meta:
        unique_together = ("turn", "territory")

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    territory = models.ForeignKey(Territory)


class Unit(models.Model):
    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)
    displaced_from = models.ForeignKey(Territory, null=True, blank=True,
                                       related_name='displaced')
    standoff_from = models.ForeignKey(Territory, null=True, blank=True,
                                      related_name='standoff')

    def __unicode__(self):
        return u'%s %s' % (self.u_type, self.subregion.territory)


class Order(models.Model):
    class Meta:
        get_latest_by = "timestamp"

    ACTION_CHOICES = (
        ('H', 'Hold'),
        ('M', 'Move'),
        ('S', 'Support'),
        ('C', 'Convoy'),
        ('B', 'Build'),
        ('D', 'Disband')
    )
    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    timestamp = models.DateTimeField(auto_now_add=True)
    slot = models.PositiveSmallIntegerField()
    actor = models.ForeignKey(Subregion, null=True, blank=True,
                              related_name='acts')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    assist = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='assisted')
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='targeted')
