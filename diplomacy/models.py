from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
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

    def consistency_check(self):
        pass

    def is_legal(self, order, units):
        pass

    def canonical_orders(self, turn):
        units = Unit.objects.filter(turn=turn)

        # the default action for each unit, if no order is defined
        orders = dict((u.id, {'government': u.government,
                              'actor': u.subregion, 'action': 'H'})
                      for u in units)

        # replace with the most recent legal order
        for o in Order.objects.filter(turn=turn):
            if self.is_legal(o, units):
                u = units.get(subregion__territory=o.actor.territory)
                assist = units.get(subregion__territory=o.assist.territory)
                orders[u] = {'id': o.id, 'government': o.government,
                             'actor': u.subregion, 'action': o.action,
                             'assist': assist.subregion, 'target': o.target}
        return orders

    def detect_civil_disorder(self, orders):
        return [gvt for gvt in self.government_set.all()
                if not any('id' in o for u, o in orders.iteritems()
                           if o['government'] == gvt)]

    def construct_dependencies(self, orders):
        dep = {}
        for (u1, o1), (u2, o2) in permutations(orders.iteritems(), 2):
            depend = False
            if o1['action'] == 'C' and o2['action'] == 'M':
                depend = (o2['target'].territory == u1.subregion.territory)
            if o1['action'] == 'S' and o2['action'] == 'C':
                depend = (u1.subregion.territory == o2['target'].territory)
            if o1['action'] == 'H' and o2['action'] == 'S':
                depend = ((u1.subregion.territory == o2['assist'].territory
                            and o2['target'] is None) or
                           (u1.subregion.territory == o2['target'].territory
                            and o2['assist'] is not None))
            if o1['action'] == 'M':
                if o2['action'] == 'S':
                    depend = (u1.subregion.territory ==
                              o2['assist'].territory)

            if depend:
                dep.setdefault(u1, []).append(u2)

    def _resolve(self, order):
        pass

    def consistent(self, state):
        pass

    def resolve(self, state, orders, dep):
        _state = set(o for o, d in state)

        # Any orders that have no more unresolved dependencies should
        # be brought into our new hypothetical order resolution.
        new_state = tuple((order, self._resolve(order)) for order in orders
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
                                for order in orders if not in _state)
        if not remaining_deps:
            return state
        # Go with the order with the fewest remaining deps.
        q, order = remaining_deps[0]

        # The order has unresolved deps which might be circular, so it
        # isn't obvious how to resolve it.  Try both ways.
        results = []
        for S in (True, False):
            results.append(self.resolve(state+((order, S),), orders, dep))

        return results[0] if results[0] else results[1]

    def update_units(self, decisions):
        pass

    def update_ownership(self):
        for t in Territory.objects.all():
            u = Unit.objects.filter(turn=turn, subregion__territory=t)
            assert u.count() < 2
            try:
                if turn.season == 'F' and u.exists():
                    gvt = u[0].government
                else:
                    gvt = self.government_set.get(
                        ownership__turn=prev, ownership__territory=t)
            except ObjectDoesNotExist:
                continue
            Ownership(turn=turn, government=gvt, territory=t).save()

    def generate(self):
        turn = self.current_turn()

        self.consistency_check()

        orders = self.canonical_orders(turn)
        disorder = self.detect_civil_disorder(orders)
        dependencies = self.construct_dependencies(orders)
        decisions = self.resolve((), orders, dependencies)

        turn = self.turn_set.create(number=turn.number+1)
        self.update_units(decisions)
        self.update_ownership()

        self.consistency_check()

    generate.alters_data = True

def game_changed(sender, **kwargs):
    instance = kwargs['instance']
    if instance.state == 'A' and not instance.turn_set.exists():
        turn = instance.turn_set.create(number=0)
        convert = {'L': 'A', 'S': 'F'}
        governments = list(instance.government_set.all())
        shuffle(governments)
        for pwr, gvt in zip(Power.objects.all(), governments):
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

class Ownership(models.Model):
    class Meta:
        unique_together = ("turn", "territory")

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    territory = models.ForeignKey(Territory)

class Unit(models.Model):
    class Meta:
        unique_together = ("turn", "subregion")

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
                              related_name='actors')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    assist = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='assists')
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='targets')
