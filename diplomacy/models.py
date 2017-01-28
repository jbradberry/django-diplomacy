from collections import defaultdict
from functools import partial
from itertools import combinations, permutations
from random import shuffle

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_save, post_save

from .engine import standard
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

        return lookup_table[t_key]

    return t_id

t_id = t_id_closure()

def subregion_id_closure():
    lookup_table = {}

    def subregion_id(sr_key):
        if not lookup_table:
            lookup_table.update((subregion_key(sr), sr.id)
                                for sr in Subregion.objects.select_related('territory'))

        return lookup_table[sr_key]

    return subregion_id

subregion_id = subregion_id_closure()

def keys_to_ids(seq):
    return [subregion_id(sr_key) for sr_key in seq]

def borders(sr_key):
    return standard.mapping.get(sr_key, ())

def find_convoys(units, fleets):
    """
    Generates pairs consisting of a cluster of adjacent non-coastal
    fleets, and the coastal territories that are reachable via convoy
    from that cluster.  This is necessary to determine legal orders.

    """
    index = {f: {f} for f in fleets}

    # Calculate the connected sets of fleets
    for f1, f2 in combinations(fleets, 2):
        # If this pair is not adjacent, ignore it
        if f2 not in borders(f1):
            continue

        # If the sets for each of these fleets are not already the same set,
        # merge them and update the index
        if index[f1] != index[f2]:
            index[f1] |= index[f2]
            index.update((x, index[f1]) for x in index[f2])

    groups = {frozenset(S) for S in index.itervalues()}

    armies = {
        u['subregion'] for u in units.itervalues()
        if u['u_type'] == 'A'
    }

    convoyable = []
    for gset in groups:
        coasts = {
            sr for f in gset
            for b in borders(f)
            for sr in standard.territories.get(territory(b), ())
            if sr[2] == 'L'
        }
        if coasts & armies:
            convoyable.append((set(gset), coasts))

    return convoyable

def detect_paradox(orders, dep):
    """
    Implements Tarjan's strongly connected components algorithm to
    find the paradoxical convoys.

    """
    dep = dict(dep)

    low = {}
    stack = []
    result = set()

    def visit(node, orders, dep):
        if node in low:
            return

        index = len(low)
        low[node] = index
        stack_pos = len(stack)
        stack.append(node)

        for w in dep.get(node, ()):
            visit(w, orders, dep)
            low[node] = min(low[node], low[w])

        if low[node] == index:
            component = tuple(stack[stack_pos:])
            del stack[stack_pos:]
            if len(component) > 1:
                result.update(c for c in component
                              if orders[c]['action'] == 'C')
            for item in component:
                low[item] = len(orders)

    for node in orders:
        visit(node, orders, dep)
    return result

def consistent(state, orders, fails, paradox, units):
    state = dict(state)

    hold_str = defaultdict(int)
    attack_str = defaultdict(int)
    defend_str = defaultdict(int)
    prevent_str = defaultdict(int)

    path = {}
    convoy = defaultdict(lambda: False) # True if this unit is successfully
                                        # convoyed, False otherwise.

    # determine if moves have a valid path
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            defend_str[T], path[T], P = 1, False, False

            # matching successful convoy orders
            matching = [
                subregion_key(orders[T2]['actor'])
                for T2, d2 in state.iteritems()
                if d2
                and orders[T2]['action'] == 'C'
                and assist(T, order, T2, orders[T2])
                and (order['government'] == orders[T2]['government']
                     or order['convoy'])
            ]
            # matching successful and paradoxical convoy orders
            p_matching = matching + [
                subregion_key(orders[T2]['actor'])
                for T2 in paradox
                if assist(T, order, T2, orders[T2])
                and order['convoy']
            ]

            # FIXME refactor
            if any(subregion_key(order['actor']) in L
                   and subregion_key(order['target']) in L
                   for F, L in find_convoys(units, matching)):
                # We have a valid convoy path if there is a chain
                # of successful convoys between our endpoints.
                path[T] = True

            # FIXME refactor
            if (not path[T] and
                any(subregion_key(order['actor']) in L
                    and subregion_key(order['target']) in L
                    for F, L in find_convoys(units, p_matching))):
                # But if there is a path when paradoxical convoys
                # are included, we have a paradox.
                P = True

            convoy[T] = path[T]
            if (not order['convoy']
                and subregion_key(order['target']) in borders(subregion_key(order['actor']))):
                # if we are adjacent to the target, we can have a
                # path even without a successful convoy, but only
                # if we don't have a paradox
                path[T] = not P

    # calculate base hold, attack, and prevent strengths
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            if path[T]:
                prevent_str[T], attack_str[T] = 1, 1

                if territory(subregion_key(order['target'])) in state:
                    T2 = territory(subregion_key(order['target']))
                    d2 = state[T2]

                    # other unit moves away
                    if (d2
                        and orders[T2]['action'] == 'M'
                        and not head_to_head(T, order, T2, orders[T2],
                                             convoy[T], convoy[T2])):
                        attack_str[T] = 1
                    # other unit is also ours
                    elif units[T]['government'] == units[T2]['government']:
                        attack_str[T] = 0

                    # prevent strength
                    if d2 and head_to_head(T, order, T2, orders[T2],
                                           convoy[T], convoy[T2]):
                        prevent_str[T] = 0

            if T in state:
                hold_str[T] = 0 if state[T] else 1

        if order['action'] in ('H', 'S', 'C'):
            hold_str[T] = 1

    # calculate additions to strengths due to support orders
    for T, d in state.iteritems():
        order = orders[T]

        if not d or order['action'] != 'S':
            continue

        if order['target'] is None:
            hold_str[territory(subregion_key(order['assist']))] += 1
        else:
            if attack_str[territory(subregion_key(order['assist']))]:
                T2 = territory(subregion_key(order['target']))
                d2 = state.get(T2, False)
                if T2 not in orders:
                    attack_str[territory(subregion_key(order['assist']))] += 1
                elif (d2
                      and orders[T2]['action'] == 'M'
                      and not head_to_head(T, order, T2, orders[T2],
                                           convoy[T], convoy[T2])):
                    attack_str[territory(subregion_key(order['assist']))] += 1
                # other unit is not ours
                elif units[T]['government'] != units[T2]['government']:
                    attack_str[territory(subregion_key(order['assist']))] += 1
            if defend_str[territory(subregion_key(order['assist']))]:
                defend_str[territory(subregion_key(order['assist']))] += 1
            if prevent_str[territory(subregion_key(order['assist']))]:
                prevent_str[territory(subregion_key(order['assist']))] += 1

    # determine if the strength calculations are consistent with the state
    for T, d in state.iteritems():
        order = orders[T]

        if order['action'] == 'M':
            target = territory(subregion_key(order['target']))
            move = True
            if (target in orders
                and head_to_head(T, order, target, orders[target],
                                 convoy[T], convoy[target])
                and attack_str[T] <= defend_str[target]):
                move = False
            if attack_str[T] <= hold_str[target]:
                move = False
            if any(attack_str[T] <= prevent_str[T2]
                   for T2, o2 in orders.iteritems()
                   if T != T2 and o2['action'] == 'M'
                   and territory(subregion_key(o2['target'])) == target):
                move = False
            if not path[T]:
                move = False
            if T in fails:
                move = False

            if d ^ move:
                return False

        if order['action'] == 'S':
            target = territory(subregion_key(order['target']))
            attackers = set(T2 for T2, o2 in orders.iteritems()
                            if o2['action'] == 'M'
                            and territory(subregion_key(o2['target'])) == T)
            cut = (T in fails
                   or (target in attackers
                       and attack_str[target] > hold_str[T])
                   or any(attack_str[T2] > 0 for T2 in attackers
                          if T2 != target))
            if d ^ (not cut):
                return False

        if order['action'] in ('H', 'C'):
            hold = True
            if T in fails:
                hold = False

            attackers = set(T2 for T2, o2 in orders.iteritems()
                            if o2['action'] == 'M'
                            and territory(subregion_key(o2['target'])) == T)
            if attackers:
                S, P, A = max((attack_str[T2], prevent_str[T2], T2)
                              for T2 in attackers)
                if S > hold_str[T] and not any(prevent_str[T2] >= S
                                               for T2 in attackers
                                               if T2 != A):
                    hold = False

            if (d != False) ^ hold:
                return False

    return True

def resolve(state, orders, dep, fails, paradox, units):
    _state = set(T for T, d in state)

    # Only bother calculating whether the hypothetical solution is
    # consistent if all orders within it have no remaining
    # unresolved dependencies.
    if all(all(o in _state for o in dep[T]) for T, d in state):
        if not consistent(state, orders, fails, paradox, units):
            return None

    # For those orders not already in 'state', sort from least to
    # most remaining dependencies.
    remaining_deps = sorted(
        (sum(1 for o in dep[T] if o not in _state), T)
        for T in orders
        if T not in _state
    )
    if not remaining_deps:
        return state
    # Go with the order with the fewest remaining deps.
    q, T = remaining_deps[0]

    # Unresolved dependencies might be circular, so it isn't
    # obvious how to resolve them.  Try both ways, with preference
    # for 'success'.
    resolutions = (None, False) if T in paradox else (True, False)
    for S in resolutions:
        result = resolve(state+((T, S),), orders, dep, fails, paradox, units)
        if result:
            return result

    return None

# End of refactor wrapper functions

def subregion_key(sr):
    if not sr:
        return None
    return (sr.territory.name, sr.subname, sr.sr_type)

def territory(sr):
    if sr is None:
        return None
    if isinstance(sr, Subregion):
        return sr.territory_id
    return sr[0]

def assist(T1, o1, T2, o2):
    return territory(subregion_key(o2['assist'])) == T1

def attack_us(T1, o1, T2, o2):
    return territory(subregion_key(o2['target'])) == T1

def attack_us_from_target(T1, o1, T2, o2):
    return (territory(subregion_key(o2['assist'])) == territory(subregion_key(o1['target']))
            and territory(subregion_key(o2['target'])) == T1)

def head_to_head(T1, o1, T2, o2, c1=False, c2=False):
    actor = o2['assist'] if o2['assist'] else o2['actor']
    T2 = territory(subregion_key(actor))
    if not any(territory(S) == T2 for S in borders(subregion_key(o1['actor']))):
        return False
    if not any(territory(S) == T1 for S in borders(subregion_key(actor))):
        return False
    if c1 or c2:
        return False
    return (territory(subregion_key(o2['target'])) == T1
            and territory(subregion_key(o1['target'])) == T2)

def hostile_assist_hold(T1, o1, T2, o2):
    return (territory(subregion_key(o2['assist'])) == territory(subregion_key(o1['target']))
            and o2['target'] is None)

def hostile_assist_compete(T1, o1, T2, o2):
    return (territory(subregion_key(o2['assist'])) != T1 and
            territory(subregion_key(o2['target'])) == territory(subregion_key(o1['target'])))

def move_away(T1, o1, T2, o2):
    return (territory(subregion_key(o1['target'])) == T2 and
            (territory(subregion_key(o2['target'])) != T1 or o1['convoy'] or o2['convoy']))


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

    def detect_civil_disorder(self, orders):
        user_issued = set(o['government'] for o in orders.itervalues()
                          if 'id' in o)
        automated = set(o['government'] for o in orders.itervalues()
                        if 'id' not in o)
        return automated - user_issued

    def construct_dependencies(self, orders):
        dep = defaultdict(list)
        for (T1, o1), (T2, o2) in permutations(orders.iteritems(), 2):
            depend = False
            act1, act2 = o1['action'], o2['action']
            if (act1, act2) in DEPENDENCIES:
                depend = any(f(T1, o1, T2, o2) for f in DEPENDENCIES[(act1, act2)])

            if depend:
                dep[T1].append(T2)

        return dep

    def resolve_retreats(self, orders):
        decisions = []
        target_count = defaultdict(int)
        for T, order in orders.iteritems():
            if order['action'] == 'M':
                target_count[territory(subregion_key(order['target']))] += 1
            else:
                decisions.append((T, None))
        for T, order in orders.iteritems():
            if order['action'] != 'M':
                continue
            if target_count[territory(subregion_key(order['target']))] == 1:
                decisions.append((T, True))
            else:
                decisions.append((T, False))
        return decisions

    def resolve_adjusts(self, orders):
        return [(T, order.get('action') is not None)
                for T, order in orders.iteritems()]

    def activate(self):
        if self.state != 'S' or self.turn_set.exists():
            return False
        if self.government_set.count() != 7:
            return False
        turn = self.turn_set.create(number=0)
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

        turn.consistency_check()

        orders = {territory(subregion_key(o['actor'])): o
                  for o in turn.normalize_orders()
                  if o['actor'] is not None}

        units = turn.get_units()

        if turn.season in ('S', 'F'):
            # FIXME: do something with civil disorder
            disorder = self.detect_civil_disorder(orders)
            dependencies = self.construct_dependencies(orders)
            paradox_convoys = detect_paradox(orders, dependencies)
            fails = turn.immediate_fails(orders)
            decisions = resolve((), orders, dependencies, fails, paradox_convoys, units)
        elif turn.season in ('SR', 'FR'):
            decisions = self.resolve_retreats(orders)
        else:
            decisions = self.resolve_adjusts(orders)
        if decisions is None:
            return False

        turn = self.turn_set.create(number=turn.number+1)
        turn.update_units(orders, decisions)
        turn.update_ownership()

        turn.consistency_check()
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

    @property
    def prev(self):
        earlier = self.game.turn_set.filter(number=self.number - 1)
        if earlier:
            return earlier.get()

    @property
    def next(self):
        later = self.game.turn_set.filter(number=self.number + 1)
        if later:
            return later.get()

    def get_units(self):
        return {
            territory(subregion_key(u.subregion)): {
                'government': u.government.power.name,
                'u_type': u.u_type,
                'subregion': subregion_key(u.subregion),
            }
            for u in self.unit_set.select_related('subregion__territory',
                                                  'government__power')
        }

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
    def valid_hold(self, actor, empty=None):
        if self.season in ('S', 'F'):
            if self.unit_set.filter(subregion=actor).count() == 1:
                return {empty: {empty: False}}
        return {}

    # FIXME refactor
    def valid_move(self, actor, empty=None):
        if self.season == 'FA':
            return {}

        unit = self.unit_set.filter(subregion=actor)
        target = Subregion.objects.filter(borders=actor)
        sr_mapping = {sr.id: subregion_key(sr)
                      for sr in Subregion.objects.select_related('territory')}

        if self.season in ('SR', 'FR'):
            # only dislodged units retreat
            unit = unit.filter(dislodged=True)
            target = target.exclude(
                # only go to empty territories ...
                territory__subregion__unit__turn=self
            ).exclude(
                # that we weren't displaced from ...
                territory__in=[
                    u.displaced_from for u in unit if u.displaced_from]
            ).exclude(
                # and that isn't empty because of a standoff.
                territory__in=[
                    u.standoff_from for u in
                    self.unit_set.filter(standoff_from__isnull=False)]
            ).distinct()

        if unit.count() != 1:
            return {}
        target = [t.id for t in target]

        convoyable = set()
        if self.season in ('S', 'F') and unit.get().u_type == 'A':
            target = set(target)
            fleets = Subregion.objects.filter(
                sr_type='S', unit__turn=self
            ).exclude(
                territory__subregion__sr_type='L'
            ).select_related('territory').distinct()
            fleets = [subregion_key(sr) for sr in fleets]
            for fset, lset in find_convoys(self.get_units(), fleets):
                if subregion_key(actor) in lset:
                    lset = set(keys_to_ids(lset))
                    target.update(lset)
                    convoyable.update(lset)
            target.discard(actor.id)

        if not target:
            return {}
        return {
            empty: {x: (x in convoyable
                        and any(sr_mapping[x] == b for b in borders(subregion_key(actor))))
                    for x in target}
        }

    # FIXME refactor
    def valid_support(self, actor, empty=None):
        if self.season not in ('S', 'F'):
            return {}
        if self.unit_set.filter(subregion=actor).count() != 1:
            return {}

        sr = Subregion.objects.all()
        adj = sr.filter(territory__subregion__borders=actor).distinct()

        # support to hold
        results = {a.id: {empty: False}
                   for a in adj.filter(unit__turn=self)}

        adj = set(subregion_key(a) for a in adj)

        # support to attack
        attackers = sr.filter(borders__territory__subregion__borders=actor,
                              unit__turn=self
                              ).exclude(id=actor.id).distinct()
        for a in attackers:
            reachable = keys_to_ids(adj & set(borders(subregion_key(a))))
            results.setdefault(a.id, {}).update((x, False) for x in reachable)

        # support to convoyed attack
        attackers = sr.filter(unit__turn=self, sr_type='L'
                              ).exclude(id=actor.id).distinct()
        fleets = Subregion.objects.filter(
            sr_type='S', unit__turn=self).exclude(
            territory__subregion__sr_type='L').exclude(
            # if we are issuing a support, we can't convoy.
            id=actor.id).distinct()
        fleets = [subregion_key(sr) for sr in fleets]

        for fset, lset in find_convoys(self.get_units(), fleets):
            for a in attackers:
                if subregion_key(a) not in lset:
                    continue
                if not (adj & lset - {subregion_key(a)}):
                    continue
                results.setdefault(a.id, {}).update(
                    (x, False)
                    for x in keys_to_ids(adj & lset - {subregion_key(a)})
                )

        return results

    # FIXME refactor
    def valid_convoy(self, actor, empty=None):
        if self.season not in ('S', 'F'):
            return {}
        if self.unit_set.filter(subregion=actor).count() != 1:
            return {}
        if actor.sr_type != 'S':
            return {}

        subr = Subregion.objects.all()
        fleets = Subregion.objects.filter(
            sr_type='S', unit__turn=self
        ).exclude(territory__subregion__sr_type='L').distinct()
        fleets = [subregion_key(sr) for sr in fleets]
        for fset, lset in find_convoys(self.get_units(), fleets):
            if subregion_key(actor) in fset:
                lset = set(keys_to_ids(lset))
                attackers = subr.filter(unit__turn=self, sr_type='L',
                                        id__in=lset).distinct()
                return {a.id: {x: False for x in lset - set([a.id])}
                        for a in attackers}
        return {}

    # FIXME refactor
    def valid_build(self, actor, empty=None):
        if not self.season == 'FA':
            return {}
        T = actor.territory
        G = T.ownership_set.get(turn=self).government
        if not (T.is_supply and G.builds_available() > 0):
            return {}
        if T.subregion_set.filter(unit__turn=self).exists():
            return {}
        if T.ownership_set.filter(turn=self,
                                  government__power=T.power).exists():
            return {empty: {empty: False}}
        return {}

    # FIXME refactor
    def valid_disband(self, actor, empty=None):
        if self.season in ('S', 'F'):
            return {}

        unit = actor.unit_set.filter(turn=self)
        if self.season in ('SR', 'FR'):
            if not unit.filter(dislodged=True).exists():
                return {}
        elif unit.get().government.builds_available() >= 0:
            return {}
        return {empty: {empty: False}}

    # FIXME
    def consistency_check(self):
        pass

    # FIXME refactor
    def is_legal(self, order):
        if isinstance(order, Order):
            order = {'government': order.post.government,
                     'turn': order.post.turn,
                     'actor': order.actor, 'action': order.action,
                     'assist': order.assist, 'target': order.target}

        if order['actor'] is None:
            if self.season != 'FA':
                return False
            units = Unit.objects.none()
        else:
            units = order['actor'].unit_set.filter(turn=self)

        if order['actor'] is None or order['action'] is None:
            return (self.season == 'FA' and
                    order['government'].builds_available() > 0)
        if order['action'] != 'B' and not units.exists():
            return False

        if self.season in ('S', 'F'):
            if units.get().government != order['government']:
                return False
        elif self.season in ('SR', 'FR'):
            units = units.filter(dislodged=True)
            if not units.exists():
                return False
            if units.get().government != order['government']:
                return False
        elif order['action'] == 'D':
            if units and units.get().government != order['government']:
                return False
        elif order['action'] == 'B':
            if not self.ownership_set.filter(
                territory__subregion=order['actor'],
                government=order['government']).exists():
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

    # FIXME refactor: The responsibility of this method should be to provide a
    # list of Order instances.  Converting these to a list of dicts for use in
    # the turn generation engine should be separate.
    def normalize_orders(self, gvt=None):
        gvts = (gvt,) if gvt else self.game.government_set.all()

        # Construct the set of default orders.  This set is exhaustive, no units
        # outside or number of builds in excess will be permitted.
        if self.season == 'FA':
            orders = {
                (g.id, s): {'government': g, 'turn': self,
                            'actor': None, 'action': None,
                            'assist': None, 'target': None,
                            'via_convoy': False, 'convoy': False}
                for g in gvts
                for s in xrange(abs(g.builds_available(self)))
            }
        else:
            action = 'H' if self.season in ('S', 'F') else None
            orders = {
                (g.id, a.id): {'government': g, 'turn': self,
                               'actor': a, 'action': action,
                               'assist': None, 'target': None,
                               'via_convoy': False, 'convoy': False}
                for g in gvts
                for a in g.actors(self)
            }

        # Find the most recent set of posted orders from each relevant government.
        posts = self.posts.all()
        if gvt:
            posts = posts.filter(government=gvt)

        most_recent = {}
        for post in posts:
            most_recent.setdefault(post.government, post)
            if post.timestamp > most_recent[post.government].timestamp:
                most_recent[post.government] = post

        # For orders that were explicitly given, replace the default order if
        # the given order is legal.  Illegal orders are dropped.
        for gvt, post in most_recent.iteritems():
            i = 0
            for o in post.orders.select_related('actor__territory',
                                                'assist__territory',
                                                'target__territory'):
                if self.is_legal(o):
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
                        'id': o.id, 'government': post.government,
                        'turn': self, 'actor': o.actor, 'action': o.action,
                        'assist': o.assist, 'target': o.target,
                        'via_convoy': o.via_convoy
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
                            assist(territory(subregion_key(o['actor'])), o,
                                   territory(subregion_key(o2['actor'])), o2)]
                gvt_matching = [o2 for g2, o2 in matching if g2 == g]

                if subregion_key(o['target']) in borders(subregion_key(o['actor'])):
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

    # FIXME refactor
    def immediate_fails(self, orders):
        results = set()
        for T, o in orders.iteritems():
            if o['action'] == 'M':
                if subregion_key(o['target']) not in borders(subregion_key(o['actor'])):
                    matching = [
                        subregion_key(o2['actor'])
                        for T2, o2 in orders.iteritems()
                        if o2['action'] == 'C'
                        and o2['assist'] == o['actor']
                        and o2['target'] == o['target']
                    ]
                    if any(subregion_key(o['actor']) in L and subregion_key(o['target']) in L
                           for F, L in find_convoys(self.get_units(), matching)):
                        continue
                else:
                    continue
            elif o['action'] not in ('S', 'C'):
                continue
            else:
                assist = orders[territory(subregion_key(o['assist']))]
                if o['target'] is not None:
                    if (assist['action'] == 'M' and
                        assist['target'] == o['target']):
                        continue
                else:
                    if assist['action'] in ('H', 'C', 'S'):
                        continue
            results.add(T)

        return results

    def create_canonical_orders(self, orders, decisions, turn):
        decisions = dict(decisions)
        keys = set(('government', 'actor', 'action',
                    'assist', 'target', 'via_convoy'))

        for T, o in orders.iteritems():
            order = {k: v for k, v in o.iteritems() if k in keys}
            order['user_issued'] = o.get('id') is not None
            if decisions.get(T):
                order['result'] = 'S'
            elif any(T in db for db in turn.disbands.itervalues()):
                order['result'] = 'D'
            elif T in turn.displaced:
                order['result'] = 'B'
            else:
                order['result'] = 'F'
            self.canonicalorder_set.create(**order)

    def _update_units_changes(self, orders, decisions, units):
        self.disbands = defaultdict(set)
        self.displaced, self.failed = {}, defaultdict(list)

        retreat = self.prev.season in ('SR', 'FR')

        for a, d in decisions:
            action = orders[a].get('action')
            # units that are displaced must retreat or be disbanded
            if retreat and action is None:
                del units[(a, retreat)]
                self.disbands[orders[a]['government'].id].add(a)
                orders[a]['action'] = 'D'
                continue

            if action == 'M':
                target = orders[a]['target']
                T = territory(subregion_key(orders[a]['actor']))
                if d: # move succeeded
                    units[(a, retreat)]['subregion'] = target
                    if not retreat:
                        self.displaced[territory(subregion_key(target))] = T
                elif retreat: # move is a failed retreat
                    del units[(a, retreat)]
                    continue
                else: # move failed
                    self.failed[territory(subregion_key(target))].append(T)

            # successful build
            if d and action == 'B':
                units[(a, False)] = {
                    'turn': self,
                    'government': orders[a]['government'],
                    'u_type': convert[orders[a]['actor'].sr_type],
                    'subregion': orders[a]['actor']
                }

            if action == 'D':
                del units[(a, retreat)]
                self.disbands[orders[a]['government'].id].add(a)
                continue

    def _update_units_blocked(self, orders, decisions, units):
        for a, d in decisions:
            key = (a, False)
            # if our location is marked as the target of a
            # successful move and we failed to move, we are displaced.
            if not d and a in self.displaced:
                units[key].update(
                    dislodged=True,
                    displaced_from_id=( # only mark a location as disallowed for
                        None         # retreats if it wasn't via convoy
                        if orders[self.displaced[a]].get('convoy')
                        else t_id(self.displaced[a])
                    )
                )
            if orders[a].get('action') != 'M':
                continue
            t = territory(subregion_key(orders[a]['target']))
            # if multiple moves to our target failed, we have a standoff.
            if len(self.failed[t]) > 1:
                units[key]['standoff_from_id'] = t_id(t)

    def _update_units_autodisband(self, orders, units):
        subr = Subregion.objects.all()
        for g in self.game.government_set.all():
            builds = g.builds_available(self.prev) + len(self.disbands[g.id])
            if builds >= 0:
                continue

            # If we've reached this point, we have more units than allowed.
            # Disband inward from the outermost unit.  For ties, disband fleets
            # first then armies, and do in alphabetical order from there, if
            # necessary.  Fleets may only count distance via water, but
            # armies may count both land and water as one space each.

            unit_distances = {
                u: [None, u.sr_type == 'L', unicode(u)]
                for u in subr.filter(unit__government=g, unit__turn=self.prev)
            }

            distance = 0
            examined = set(sc for sc in
                           subr.filter(territory__power=g.power,
                                       territory__is_supply=True,
                                       sr_type='S'))
            while any(not D[1] and D[0] is None
                      for D in unit_distances.itervalues()):
                for u, D in unit_distances.iteritems():
                    if not D[1] and D[0] is None and u in examined:
                        D[0] = -distance  # We want them reversed by distance,
                adj = set(                # but non-reversed by name.
                    s for s in subr.filter(
                        borders__in=examined
                    ).exclude(id__in=[se.id for se in examined]).distinct()
                )
                examined |= adj
                distance += 1

            distance = 0
            examined = set(sc for sc in
                           subr.filter(territory__power=g.power,
                                       territory__is_supply=True))
            while any(D[1] and D[0] is None
                      for D in unit_distances.itervalues()):
                for u, D in unit_distances.iteritems():
                    if D[1] and D[0] is None and u in examined:
                        D[0] = -distance  # We want them reversed by distance,
                adj = set(                # but non-reversed by name.
                    s for s in subr.filter(
                        territory__subregion__borders__in=examined
                    ).exclude(id__in=[se.id for se in examined]).distinct()
                )
                examined |= adj
                distance += 1

            for u in sorted(unit_distances, key=lambda x: unit_distances[x]):
                if territory(subregion_key(u)) in self.disbands[g.id]:
                    continue

                orders[territory(subregion_key(u))] = {'government': g, 'actor': u,
                                                       'action': 'D', 'assist': None,
                                                       'target': None, 'via_convoy': False}
                del units[(territory(subregion_key(u)), False)]
                self.disbands[g.id].add(territory(subregion_key(u)))
                builds += 1
                if builds == 0:
                    break

    def update_units(self, orders, decisions):
        units = {
            (territory(subregion_key(u.subregion)), x): {
                'turn': self, 'government': u.government,
                'u_type': u.u_type, 'subregion': u.subregion,
                'previous': u
            }
            for x in (True, False) # dislodged or not
            for u in self.prev.unit_set.filter(dislodged=x)
        }

        self._update_units_changes(orders, decisions, units)

        if self.prev.season in ('S', 'F'):
            self._update_units_blocked(orders, decisions, units)

        if self.prev.season == 'FA':
            self._update_units_autodisband(orders, units)

        self.prev.create_canonical_orders(orders, decisions, self)

        for k, u in units.iteritems():
            Unit.objects.create(**u)

    # FIXME refactor: this method should take data calculated by the
    # engine and create the new ownership objects based on that.
    def update_ownership(self):
        for t in Territory.objects.filter(subregion__sr_type='L'):
            u = self.unit_set.filter(subregion__territory=t)

            try:
                if self.season == 'FA' and u.exists():
                    gvt = u[0].government
                else:
                    gvt = self.prev.ownership_set.get(territory=t).government
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
        if turn is None:
            return Subregion.objects.none()

        if turn.season == 'FA' and self.builds_available() > 0:
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
        if getattr(turn, 'season', '') == 'FA':
            return abs(self.builds_available(turn))
        return self.actors(turn).count()

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
