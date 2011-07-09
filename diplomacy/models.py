from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from random import shuffle
from itertools import permutations
from collections import defaultdict
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

convert = {'L': 'A', 'S': 'F'}

def territory(sr):
    if sr is None:
        return None
    return sr.territory.id

def assist(T1, o1, T2, o2):
    return territory(o2['assist']) == T1

def attack_us(T1, o1, T2, o2):
    return territory(o2['target']) == T1

def attack_us_from_target(T1, o1, T2, o2):
    return (territory(o2['assist']) == territory(o1['target']) and
            territory(o2['target']) == T1)

def head_to_head(T1, o1, T2, o2, c1=False, c2=False):
    actor = o2['assist'] if o2['assist'] else o2['actor']
    T2 = territory(actor)
    if not any(territory(S) == T2 for S in o1['actor'].borders.all()):
        return False
    if not any(territory(S) == T1 for S in actor.borders.all()):
        return False
    if c1 or c2:
        return False
    return territory(o2['target']) == T1 and territory(o1['target']) == T2

def hostile_assist_hold(T1, o1, T2, o2):
    return o2['assist'] == o1['target'] and o2['target'] is None

def hostile_assist_compete(T1, o1, T2, o2):
    return (territory(o2['assist']) != T1 and
            territory(o2['target']) == territory(o1['target']))

def move_away(T1, o1, T2, o2):
    return (territory(o1['target']) == T2 and
            (territory(o2['target']) != T1 or o1['convoy'] or o2['convoy']))


DEPENDENCIES = {('C', 'M'): (attack_us,),
                ('S', 'C'): (attack_us,),
                ('S', 'S'): (assist, attack_us_from_target),
                ('C', 'S'): (assist,),
                ('H', 'S'): (assist, attack_us),
                ('H', 'C'): (attack_us,),
                ('M', 'S'): (assist, hostile_assist_compete,
                             head_to_head, hostile_assist_hold),
                ('M', 'C'): (assist, hostile_assist_compete),
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
        dep = defaultdict(list)
        for (T1, o1), (T2, o2) in permutations(orders.iteritems(), 2):
            if (o1['action'], o2['action']) == ('M', 'C'):
                if assist(T1, o1, T2, o2):
                    o1['convoy'] = True
        for (T1, o1), (T2, o2) in permutations(orders.iteritems(), 2):
            depend = False
            act1, act2 = o1['action'], o2['action']
            if (act1, act2) in DEPENDENCIES:
                depend = any(f(T1, o1, T2, o2) for f in
                             DEPENDENCIES[(act1, act2)])

            if depend:
                dep[T1].append(T2)

        return dep

    def detect_paradox(self, orders, dep):
        """
        Implements Tarjan's strongly connected components algorithm to
        find the paradoxical convoys.

        """
        dep = dict(dep)

        low = {}
        stack = []
        result = []

        def visit(node, orders, dep):
            if node in low:
                return

            index = len(low)
            low[node] = index
            stack_pos = len(stack)
            stack.append(node)

            if node in dep:
                for w in dep[node]:
                    visit(w, orders, dep)
                    low[node] = min(low[node], low[w])

            if low[node] == index:
                component = tuple(stack[stack_pos:])
                del stack[stack_pos:]
                if len(component) > 1:
                    result.extend(c for c in component
                                  if orders[c]['action'] == 'C')
                for item in component:
                    low[item] = len(orders)

        for node in orders:
            visit(node, orders, dep)
        return result

    def consistent(self, state, orders):
        state = dict(state)

        turn = self.current_turn()

        hold_str = defaultdict(int)
        attack_str = defaultdict(int)
        defend_str = defaultdict(int)
        prevent_str = defaultdict(int)
        path, convoy = {}, defaultdict(lambda: False)

        for T, order in orders.iteritems():
            if order['action'] == 'M':
                defend_str[T], path[T] = 1, True

                # determine if we have a valid convoy path
                matching = [orders[T2]['actor'].id
                            for T2, d2 in state.iteritems()
                            if d2 and orders[T2]['action'] == 'C' and
                            assist(T, order, T2, orders[T2]) and
                            (order['government'] == orders[T2]['government']
                             or order['foreign'])]
                matching = Subregion.objects.filter(id__in=matching)
                if not any(order['actor'].id in L and
                           order['target'].id in L
                           for F, L in turn.find_convoys(matching)):
                    path[T] = False

                convoy[T] = path[T]
                if order['target'] in order['actor'].borders.all():
                    path[T] = True

        for T, order in orders.iteritems():
            if order['action'] == 'M':
                if path[T]:
                    prevent_str[T], attack_str[T] = 1, 1

                    if territory(order['target']) in state:
                        T2 = territory(order['target'])
                        d2 = state[T2]

                        # other unit moves away
                        if (d2 and orders[T2]['action'] == 'M' and not
                            head_to_head(T, order, T2, orders[T2],
                                         convoy[T], convoy[T2])):
                            attack_str[T] = 1
                        # other unit is also ours
                        elif (Government.objects.filter(
                                unit__turn=turn,
                                unit__subregion__territory__id__in=(T,T2)
                                ).distinct().count() == 1):
                            attack_str[T] = 0

                        # prevent strength
                        if d2 and head_to_head(T, order, T2, orders[T2],
                                               convoy[T], convoy[T2]):
                            prevent_str[T] = 0

                if T in state:
                    hold_str[T] = 0 if state[T] else 1

            if order['action'] in ('H', 'S', 'C'):
                hold_str[T] = 1

        for T, d in state.iteritems():
            order = orders[T]

            if not d or order['action'] != 'S':
                continue

            if order['target'] is None:
                hold_str[territory(order['assist'])] += 1
            else:
                if attack_str[territory(order['assist'])]:
                    T2 = territory(order['target'])
                    d2 = state.get(T2, False)
                    if T2 not in orders:
                        attack_str[territory(order['assist'])] += 1
                    elif (d2 and orders[T2]['action'] == 'M' and not
                          head_to_head(T, order, T2, orders[T2],
                                       convoy[T], convoy[T2])):
                        attack_str[territory(order['assist'])] += 1
                    elif (Government.objects.filter(
                            unit__turn=turn,
                            unit__subregion__territory__id__in=(T,T2)
                            ).distinct().count() != 1):
                        attack_str[order['assist'].territory.id] += 1
                if defend_str[territory(order['assist'])]:
                    defend_str[territory(order['assist'])] += 1
                if prevent_str[territory(order['assist'])]:
                    prevent_str[territory(order['assist'])] += 1

        for T, d in state.iteritems():
            order = orders[T]

            if order['action'] == 'M':
                target = territory(order['target'])
                move = True
                if (target in orders and
                    head_to_head(T, order, target, orders[target],
                                 convoy[T], convoy[target]) and
                    attack_str[T] <= defend_str[target]):
                    move = False
                if attack_str[T] <= hold_str[target]:
                    move = False
                if any(attack_str[T] <= prevent_str[T2]
                       for T2, o2 in orders.iteritems()
                       if T != T2 and o2['action'] == 'M' and
                       territory(o2['target']) == target):
                    move = False
                if not path[T]:
                    move = False

                if d ^ move:
                    return False

            if order['action'] == 'S':
                o = orders.get(territory(order['assist']), None)
                unmatched = False
                if o is None:
                    unmatched = True
                elif o['action'] == 'M' and o['target'] != order['target']:
                    unmatched = True
                elif (o['action'] in ('H', 'S', 'C') and
                      order['target'] is not None):
                    unmatched = True

                target = territory(order['target'])
                attackers = set(T2 for T2, o2 in orders.iteritems()
                                if o2['action'] == 'M' and
                                territory(o2['target']) == T)
                cut = (unmatched or
                       (target in attackers and
                        attack_str[target] > hold_str[T]) or
                       any(attack_str[T2] > 0 for T2 in attackers
                           if T2 != target))
                if d ^ (not cut):
                    return False

            if order['action'] in ('H', 'C'):
                hold = True
                attackers = set(T2 for T2, o2 in orders.iteritems()
                                if o2['action'] == 'M' and
                                territory(o2['target']) == T)
                if not attackers:
                    if not d:
                        return False
                    continue
                S, P, A = max((attack_str[T2], prevent_str[T2], T2)
                              for T2 in attackers)
                if S > hold_str[T] and not any(prevent_str[T2] >= S
                                               for T2 in attackers if T2 != A):
                    hold = False

                if (d != False) ^ hold:
                    return False

        return True

    def resolve(self, state, orders, dep, paradox):
        _state = set(T for T, d in state)

        # Only bother calculating whether the hypothetical solution is
        # consistent if all orders within it have no remaining
        # unresolved dependencies.
        if all(all(o in _state for o in dep[T]) for T, d in state):
            if not self.consistent(state, orders):
                return ()

        # For those orders not already in 'state', sort from least to
        # most remaining dependencies.
        remaining_deps = sorted((sum(1 for o in dep[T]
                                     if o not in _state), T)
                                for T in orders if T not in _state)
        if not remaining_deps:
            return state
        # Go with the order with the fewest remaining deps.
        q, T = remaining_deps[0]

        # Unresolved dependencies might be circular, so it isn't
        # obvious how to resolve them.  Try both ways, with preference
        # for 'success'.
        resolutions = (None, False) if T in paradox else (True, False)
        for S in resolutions:
            result = self.resolve(state+((T, S),), orders, dep, paradox)
            if result:
                return result

        return ()

    def resolve_retreats(self, orders):
        decisions = []
        target_count = defaultdict(int)
        for T, order in orders.iteritems():
            if order['action'] == 'M':
                target_count[T] += 1
            else:
                decisions.append((T, None))
        for T, order in orders.iteritems():
            if order['action'] != 'M':
                continue
            if target_count[T] == 1:
                decisions.append((T, True))
            else:
                decisions.append((T, False))
        return decisions

    # FIXME
    def resolve_adjusts(self, orders):
        pass

    def generate(self):
        turn = self.current_turn()

        turn.consistency_check()

        orders = dict((territory(o['actor']), o)
                      for o in turn.canonical_orders())
        if turn.season in ('S', 'F'):
            # FIXME: do something with civil disorder
            disorder = self.detect_civil_disorder(orders)
            dependencies = self.construct_dependencies(orders)
            paradox_convoys = self.detect_paradox(orders, dependencies)
            state = turn.immediate_fails(orders)
            decisions = self.resolve(state, orders, dependencies,
                                     paradox_convoys)
        elif turn.season in ('SR', 'FR'):
            decisions = self.resolve_retreats(orders)
        else:
            decisions = self.resolve_adjusts(orders)

        turn = self.turn_set.create(number=turn.number+1)
        turn.update_units(orders, decisions)
        turn.update_ownership()

        turn.consistency_check()

    generate.alters_data = True


def game_changed(sender, **kwargs):
    instance = kwargs['instance']
    if instance.state == 'A' and not instance.turn_set.exists():
        turn = instance.turn_set.create(number=0)
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

    def find_convoys(self, fleets=None):
        """
        Generates pairs consisting of a cluster of adjacent non-coastal
        fleets, and the coastal territories that are reachable via convoy
        from that cluster.  This is necessary to determine legal orders.

        """
        if fleets is None:
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
        convoyable = []
        for g in groups:
            coasts = Subregion.objects.filter(
                sr_type='L', territory__subregion__borders__id__in=g
                ).distinct()
            if coasts.filter(unit__turn=self).exists():
                convoyable.append((g, set(sr.id for sr in coasts)))
        return convoyable

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
                territory__in=[u.displaced_from for u in unit]).exclude(
                # and that isn't empty because of a standoff.
                territory__in=[u.standoff_from for u in self.unit_set.filter(
                        standoff_from__isnull=False)]).distinct()

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
        attackers = sr.filter(borders__territory__subregion__borders=actor,
                              unit__turn=self
                              ).exclude(id=actor.id).distinct()
        for a in attackers:
            reachable = adj & set(t.id for t in a.borders.all())
            results.setdefault(a.id, []).extend(reachable)

        # support to convoyed attack
        attackers = sr.filter(unit__turn=self, sr_type='L'
                              ).exclude(id=actor.id).distinct()
        fleets = Subregion.objects.filter(
            sr_type='S', unit__turn=self).exclude(
            territory__subregion__sr_type='L').exclude(
            # if we are issuing a support, we can't convoy.
            id=actor.id).distinct()

        for fset, lset in self.find_convoys(fleets):
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
            if actor.id in fset:
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
            if not unit.filter(displaced_from__isnull=False).exists():
                return {}
        elif unit.get().government.builds_available() >= 0:
            return {}
        return {empty: [empty]}

    # FIXME
    def consistency_check(self):
        pass

    def is_legal(self, order):
        if isinstance(order, Order):
            order = {'government': order.government, 'turn': order.turn,
                     'actor': order.actor, 'action': order.action,
                     'assist': order.assist, 'target': order.target}
        units = order['actor'].unit_set.filter(turn=self)
        if order['action'] != 'B' and not units.exists():
            return False

        if self.season in ('S', 'F'):
            if units.get().government != order['government']:
                return False
        elif self.season in ('SR', 'FR'):
            units = units.filter(displaced_from__isnull=False)
            if not units.exists():
                return False
            if units.get().government != order['government']:
                return False
        elif order['action'] == 'D':
            if units.get().government != order['government']:
                return False
        elif order['action'] == 'B':
            if not order['government'].owns.filter(
                turn=self, territory__subregion=order['actor']).exists():
                return False

        actions = {'H': self.valid_hold,
                   'M': self.valid_move,
                   'S': self.valid_support,
                   'C': self.valid_convoy,
                   'B': self.valid_build,
                   'D': self.valid_disband}
        tree = actions[order['action']](order['actor'])
        if not tree or getattr(order['assist'], 'id', None) not in tree:
            return False
        tree = tree[getattr(order['assist'], 'id', None)]
        if getattr(order['target'], 'id', None) not in tree:
            return False
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
                            'actor': a, 'action': action,
                            'assist': None, 'target': None,
                            'via_convoy': False, 'convoy': False})
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
                    'assist': o.assist, 'target': o.target,
                    'via_convoy': o.via_convoy and o.action == 'M' and
                    o.actor.sr_type == 'L' and self.season in ('S', 'F') and
                    o.target in o.actor.borders.all()}
        if self.season in ('S', 'F'):
            for (g, slot), o in orders.iteritems():
                if o['action'] != 'M':
                    continue
                matching = [(g2, o2) for (g2, s2), o2 in orders.iteritems()
                            if o2['action'] == 'C' and
                            assist(territory(o['actor']), o,
                                   territory(o2['actor']), o2)]
                if o['target'] not in o['actor'].borders.all():
                    o['convoy'] = bool(matching)
                    o['foreign'] = o['convoy']
                else:
                    o['convoy'] = any(g == g2 or o['via_convoy']
                                      for g2, o2 in matching)
                    o['foreign'] = o['via_convoy']
        return [v for k, v in sorted(orders.iteritems())]

    def immediate_fails(self, orders):
        results = ()
        for T, o in orders.iteritems():
            if o['action'] == 'M':
                if o['target'] not in o['actor'].borders.all():
                    matching = [o2['actor'].id for T2, o2 in orders.iteritems()
                                if o2['action'] == 'C' and
                                o2['assist'] == o['actor'] and
                                o2['target'] == o['target']]
                    matching = Subregion.objects.filter(id__in=matching)
                    if any(o['actor'].id in L and o['target'].id in L
                           for F, L in self.find_convoys(matching)):
                        continue
                else:
                    continue
            elif o['action'] not in ('S', 'C'):
                continue
            else:
                assist = orders[territory(o['assist'])]
                if o['target'] is not None:
                    if (assist['action'] == 'M' and
                        assist['target'] == o['target']):
                        continue
                else:
                    if assist['action'] in ('H', 'C', 'S'):
                        continue
            results = results + ((T, False),)

        return results

    def _update_units_changes(self, orders, decisions, units):
        self.disbands = defaultdict(set)
        self.displaced, self.failed = {}, defaultdict(list)

        retreat = self.prev.season in ('SR', 'FR')

        for a, d in decisions:
            # units that are displaced must retreat or be disbanded
            if retreat and orders[a]['action'] == None:
                del units[(a, retreat)]
                self.disbands[orders[a]['government'].id].add(a)
                continue

            if orders[a]['action'] == 'M':
                t = orders[a]['target']
                if d: # move succeeded
                    units[(a, retreat)]['subregion'] = t
                    if not retreat:
                        self.displaced[territory(t)] = orders[a]['actor']
                elif retreat: # move is a failed retreat
                    del units[(a, retreat)]
                    continue
                else: # move failed
                    self.failed[territory(t)].append(orders[a]['actor'])

            # successful build
            if d and orders[a]['action'] == 'B':
                units[(a, False)] = {'turn': self,
                                     'government': orders[a]['government'],
                                     'u_type':
                                         convert[orders[a]['actor'].sr_type],
                                     'subregion': orders[a]['actor']}

            if orders[a]['action'] == 'D':
                del units[(a, retreat)]
                self.disbands[orders[a]['government'].id].add(a)
                continue

    def _update_units_blocked(self, orders, decisions, units):
        for a, d in decisions:
            key = (a, False)
            # if our location is marked as the target of a
            # successful move, we are displaced.
            if a in self.displaced:
                units[key]['displaced_from'] = self.displaced[a].territory
            if orders[a]['action'] != 'M':
                continue
            t = orders[a]['target'].territory
            # if multiple moves to our target failed, we have a standoff.
            if len(self.failed[t.id]) > 1:
                units[key]['standoff_from'] = t

    def _update_units_autodisband(self):
        sr = Subregion.objects.all()
        for g in self.game.government_set.all():
            builds = g.builds_available(prev) + len(self.disbands[g.id])
            if builds >= 0:
                continue

            # If we've reached this point, we have more units than
            # allowed.  Disband inward from the outermost unit.
            # For ties, disband fleets first then armies, and do
            # in alphabetical order from there, if necessary.
            g_names = dict((u.id, (u.sr_type, unicode(u))) for u in
                           sr.filter(unit__government=g, unit__turn=prev))
            g_units = set(g_names.iterkeys())
            examined = set(sc.id for sc in
                           sr.filter(territory__power=g.power,
                                     territory__is_supply=True))
            u_distance = [list(examined)]
            while any(u not in examined for u in g_units):
                adj = set(s.id for s in
                          sr.filter(borders__in=examined
                                    ).exclude(id__in=examined).distinct())
                u_distance.append(list(adj))
                examined |= adj

            while builds < 0:
                current = sorted(u_distance.pop(),
                                 key=lambda x: g_names[x])
                for x in current:
                    del units[(a, False)]
                    builds += 1
                    if builds == 0:
                        break

    def update_units(self, orders, decisions):
        self.prev = Turn.objects.get(number=self.number-1)

        orders = dict(orders)
        units = dict(((territory(u.subregion), x),
                      {'turn': self, 'government': u.government,
                       'u_type': u.u_type, 'subregion': u.subregion})
                     for x in (True, False) # displaced or not
                     for u in
                     self.prev.unit_set.filter(displaced_from__isnull=not x))

        self._update_units_changes(orders, decisions, units)

        if self.prev.season in ('S', 'F'):
            self._update_units_blocked(orders, decisions, units)

        if self.prev.season == 'FA':
            self._update_units_autodisband()

        for k, u in units.iteritems():
            Unit.objects.create(**u)

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

    @classmethod
    def is_same(cls, *subregions):
        if not all(subregions):
            return False
        subregions = [sr.id if isinstance(sr, Subregion) else sr
                      for sr in subregions]
        return cls.objects.filter(subregion__id__in=subregions
                                  ).distinct().count() == 1


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

    def builds_available(self, turn=None):
        return self.supplycenters(turn) - self.units(turn)

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
    #previous = models.ForeignKey("self", null=True, blank=True)
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
    via_convoy = models.BooleanField()

    def __unicode__(self):
        result = "%s %s %s" % (convert[self.actor.sr_type], self.actor,
                               self.action)
        if self.assist:
            result += " %s %s" % (convert[self.assist.sr_type], self.assist)
        if self.target:
            result += " %s" % self.target
        if self.via_convoy:
            result += " via Convoy"
        return result
