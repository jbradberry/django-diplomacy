from collections import defaultdict, Counter
from itertools import combinations, permutations

from . import standard
from .compare import assist, head_to_head, construct_dependencies
from .utils import convert, territory, borders, territory_parts


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

    armies = {u['subregion'] for u in units if u['u_type'] == 'A'}

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

def immediate_fails(orders, units):
    results = set()
    for T, o in orders.iteritems():
        if o['action'] == 'M':
            if o['target'] not in borders(o['actor']):
                matching = [
                    o2['actor']
                    for T2, o2 in orders.iteritems()
                    if o2['action'] == 'C'
                    and o2['assist'] == o['actor']
                    and o2['target'] == o['target']
                ]
                if any(o['actor'] in L and o['target'] in L
                       for F, L in find_convoys(units, matching)):
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
        results.add(T)

    return results

def consistent(state, orders, fails, paradox, units):
    state = dict(state)
    unit_index = {territory(u['subregion']): u for u in units}

    hold_str = defaultdict(int)
    attack_str = defaultdict(int)
    defend_str = defaultdict(int)
    prevent_str = defaultdict(int)

    path = {}
    # True if this unit is successfully convoyed, False otherwise.
    convoy = defaultdict(lambda: False)

    # determine if moves have a valid path
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            defend_str[T], path[T], P = 1, False, False

            # matching successful convoy orders
            matching = [
                orders[T2]['actor'] for T2, d2 in state.iteritems()
                if d2
                and orders[T2]['action'] == 'C'
                and assist(T, order, T2, orders[T2])
                and (order['government'] == orders[T2]['government']
                     or order['convoy'])
            ]
            # matching successful and paradoxical convoy orders
            p_matching = matching + [
                orders[T2]['actor'] for T2 in paradox
                if assist(T, order, T2, orders[T2])
                and order['convoy']
            ]

            if any(order['actor'] in L and order['target'] in L
                   for F, L in find_convoys(units, matching)):
                # We have a valid convoy path if there is a chain
                # of successful convoys between our endpoints.
                path[T] = True

            if (not path[T] and
                any(order['actor'] in L and order['target'] in L
                    for F, L in find_convoys(units, p_matching))):
                # But if there is a path when paradoxical convoys
                # are included, we have a paradox.
                P = True

            convoy[T] = path[T]
            if not order['convoy'] and order['target'] in borders(order['actor']):
                # if we are adjacent to the target, we can have a
                # path even without a successful convoy, but only
                # if we don't have a paradox
                path[T] = not P

    # calculate base hold, attack, and prevent strengths
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            if path[T]:
                prevent_str[T], attack_str[T] = 1, 1

                if territory(order['target']) in state:
                    T2 = territory(order['target'])
                    d2 = state[T2]

                    # other unit moves away
                    if (d2
                        and orders[T2]['action'] == 'M'
                        and not head_to_head(T, order, T2, orders[T2],
                                             convoy[T], convoy[T2])):
                        attack_str[T] = 1
                    # other unit is also ours
                    elif unit_index[T]['government'] == unit_index[T2]['government']:
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
            hold_str[territory(order['assist'])] += 1
        else:
            if attack_str[territory(order['assist'])]:
                T2 = territory(order['target'])
                d2 = state.get(T2, False)
                if T2 not in orders:
                    attack_str[territory(order['assist'])] += 1
                elif (d2
                      and orders[T2]['action'] == 'M'
                      and not head_to_head(T, order, T2, orders[T2],
                                           convoy[T], convoy[T2])):
                    attack_str[territory(order['assist'])] += 1
                # other unit is not ours
                elif unit_index[T]['government'] != unit_index[T2]['government']:
                    attack_str[territory(order['assist'])] += 1
            if defend_str[territory(order['assist'])]:
                defend_str[territory(order['assist'])] += 1
            if prevent_str[territory(order['assist'])]:
                prevent_str[territory(order['assist'])] += 1

    # determine if the strength calculations are consistent with the state
    for T, d in state.iteritems():
        order = orders[T]

        if order['action'] == 'M':
            target = territory(order['target'])
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
                   and territory(o2['target']) == target):
                move = False
            if not path[T]:
                move = False
            if T in fails:
                move = False

            if d ^ move:
                return False

        if order['action'] == 'S':
            target = territory(order['target'])
            attackers = set(T2 for T2, o2 in orders.iteritems()
                            if o2['action'] == 'M'
                            and territory(o2['target']) == T)
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
                            and territory(o2['target']) == T)
            if attackers:
                S, P, A = max((attack_str[T2], prevent_str[T2], T2)
                              for T2 in attackers)
                if S > hold_str[T] and not any(prevent_str[T2] >= S
                                               for T2 in attackers
                                               if T2 != A):
                    hold = False

            if (d is not False) ^ hold:
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
        result = resolve(state + ((T, S),), orders, dep, fails, paradox, units)
        if result:
            return result

    return None

def resolve_retreats(orders):
    decisions = []
    target_count = defaultdict(int)
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            target_count[territory(order['target'])] += 1
        else:
            decisions.append((T, None))
    for T, order in orders.iteritems():
        if order['action'] != 'M':
            continue
        if target_count[territory(order['target'])] == 1:
            decisions.append((T, True))
        else:
            decisions.append((T, False))
    return decisions

def resolve_adjusts(orders):
    return [(T, order.get('action') is not None)
            for T, order in orders.iteritems()]

def supplycenters(owns):
    counts = Counter(o['government'] for o in owns
                     if o['is_supply'])
    return counts

def builds_available(units, owns):
    builds = defaultdict(int)
    builds.update(supplycenters(owns))

    for u in units:
        builds[u['government']] -= 1

    return builds

def actionable_subregions(turn, units, owns):
    """Returns lists of subregions that would be legal actors this turn,
    indexed by government.  These lists are not constrained by the
    number of builds available during Fall Adjustment turns, merely by
    whether the home supply center would fit the criteria.

    """
    if turn['season'] in ('S', 'F'):
        return {
            government: [u['subregion'] for u in units
                         if u['government'] == government]
            for government in standard.powers
        }
    elif turn['season'] in ('SR', 'FR'):
        return {
            government: [u['subregion'] for u in units
                         if u['dislodged'] and u['government'] == government]
            for government in standard.powers
        }
    elif turn['season'] == 'FA':
        builds = builds_available(units, owns)
        actors_index = {}
        for government in standard.powers:
            if builds.get(government, 0) > 0:
                # If we have more supply centers than units, we can build.  If,
                # - we own a supply center
                # - that is one of our original supply centers
                # - and that is not occupied by a unit
                owned_sc = (o['territory'] for o in owns
                            if o['is_supply'] and o['government'] == government)
                occupied = {territory(u['subregion']) for u in units}
                actors_index[government] = [
                    sr for T in owned_sc
                    for sr in territory_parts(T)
                    if standard.definition[T][0] == government
                    and T not in occupied
                ]
            elif builds.get(government, 0) == 0:
                actors_index[government] = []
            else:
                actors_index[government] = [u['subregion'] for u in units
                                            if u['government'] == government]

        return actors_index
    return {}

def normalize_orders(turn, orders, units, owns):
    """Returns a list of order dicts, taken from the orders previously
    submitted this turn, filtered down by legality and refilled with
    defaults.  This list is exhaustive, no units not covered by the
    list or number of builds in excess will be permitted.

    """
    from .check import is_legal  # FIXME
    actors = actionable_subregions(turn, units, owns)

    # Construct the set of default orders.  This will be the fully constrained set.
    if turn['season'] == 'FA':
        builds = builds_available(units, owns)
        orders_index = {
            (government, index): {
                'government': government, 'actor': None,
                'action': None, 'assist': None, 'target': None,
                'via_convoy': False, 'convoy': False, 'user_issued': False
            }
            for government, B in builds.iteritems()
            for index in xrange(-B if B < 0 else min(B, len(actors.get(government, ()))))
        }
    else:
        action = 'H' if turn['season'] in ('S', 'F') else None
        orders_index = {
            (government, a): {
                'government': government, 'actor': a,
                'action': action, 'assist': None, 'target': None,
                'via_convoy': False, 'convoy': False, 'user_issued': False
            }
            for government, actor_set in actors.iteritems()
            for a in actor_set
        }

    # For orders that were explicitly given, replace the default order if
    # the given order is legal.  Illegal orders are dropped.
    index = {}
    for o in orders:
        if is_legal(o, units, owns, turn['season']):
            i = o['actor']
            if turn['season'] == 'FA':
                index.setdefault(o['government'], 0)
                i = index[o['government']]
                index[o['government']] += 1

            # Drop the order if it falls outside of the set of
            # allowable acting units or build quantity.
            if (o['government'], i) not in orders_index:
                continue

            o['user_issued'], o['convoy'] = True, False
            orders_index[(o['government'], i)] = o

    if turn['season'] in ('S', 'F'):
        for (g, i), o in orders_index.iteritems():
            # This block concerns the convoyability of units, so if the unit
            # isn't moving or isn't an army, ignore it.
            if o['action'] != 'M' or o['actor'][2] != 'L':
                continue

            # Find all of the convoy orders that match the current move,
            # both overall and specifically by this user's government.
            matching = [
                (g2, o2) for (g2, i2), o2 in orders_index.iteritems()
                if o2['action'] == 'C'
                and assist(territory(o['actor']), o, territory(o2['actor']), o2)
            ]
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

    return [v for k, v in sorted(orders_index.iteritems())]

def update_retreats(orders, units):
    new_units = []
    for u in units:
        T = territory(u['subregion'])
        if T not in orders or not u['dislodged']:
            new_units.append(u)
            continue

        order = orders[T]
        if order['action'] is None:
            order['action'] = 'D'

        # units that are displaced must retreat or be disbanded
        if order['action'] == 'M' and order['result'] == 'S':
            u['subregion'] = order['target']
            new_units.append(u)
        else:
            order['result'] = 'D'

    return new_units

def update_movements(orders, units):
    displaced, failed = {}, defaultdict(int)
    for u in units:
        T = territory(u['subregion'])
        order = orders[T]
        if order['action'] == 'M':
            if order['result'] == 'S':
                u['subregion'] = order['target']
                # if the move succeeded, any unit occupying the target
                # territory will be displaced
                displaced[territory(order['target'])] = T
            else:
                failed[territory(order['target'])] += 1

    for u in units:
        T = territory(u['previous'])
        order = orders[T]
        if T in displaced and not (order['action'] == 'M' and order['result'] == 'S'):
            order['result'] = 'B'
            u.update(
                dislodged=True,
                # only mark a location as disallowed for retreats if it
                # wasn't via convoy.
                displaced_from=(
                    None if orders[displaced[T]].get('convoy') else displaced[T])
            )

        target = territory(order['target'])
        # if multiple moves to our target failed, we have a standoff
        if order['action'] == 'M' and failed[target] > 1:
            u['standoff_from'] = target

    return units

def update_adjusts(orders, units):
    new_units = []
    for u in units:
        T = territory(u['subregion'])
        order = orders.get(T, {})
        if order.get('action') == 'D':
            order['result'] = 'D'
        else:
            new_units.append(u)

    for T, o in orders.iteritems():
        if o['action'] == 'B' and o['result'] == 'S':
            new_units.append({
                'government': o['government'],
                'u_type': convert[o['actor'][2]],
                'subregion': o['actor'],
                'previous': None,
                'dislodged': False,
                'displaced_from': None,
                'standoff_from': None,
            })

    return new_units

def update_autodisbands(orders, units, owns):
    builds = builds_available(units, owns)
    autodisbands = set()
    for gvt, count in builds.iteritems():
        if count >= 0:
            continue

        # If we've reached this point, this government has more units than
        # allowed.  Disband inward from the outermost unit.  For ties,
        # disband fleets first then armies, and do in alphabetical order from
        # there, if necessary.  Fleets may only count distance via water, but
        # armies may count both land and water as one space each.

        unit_distances = [
            [None, u['u_type'] == 'A', territory(u['subregion']), u]
            for u in units
            if u['government'] == gvt
        ]

        distance = 0
        examined = {
            sr for T, (power, sc, _) in standard.definition.iteritems()
            for sr in territory_parts(T)
            if sr[2] == 'S' and sc
            and power == gvt
        }
        while any(not is_army and D is None
                  for D, is_army, name, u in unit_distances):
            for data in unit_distances:
                D, is_army, name, u = data
                if not is_army and D is None and u['subregion'] in examined:
                    # We want them reversed by distance, but non-reversed by name.
                    data[0] = -distance
            adj = {b for sr in examined for b in borders(sr)}
            examined |= adj
            distance += 1

        distance = 0
        examined = {
            sr for T, (power, sc, _) in standard.definition.iteritems()
            for sr in territory_parts(T)
            if sc and power == gvt
        }
        while any(is_army and D is None
                  for D, is_army, name, u in unit_distances):
            for data in unit_distances:
                D, is_army, name, u = data
                if is_army and D is None and u['subregion'] in examined:
                    # We want them reversed by distance, but non-reversed by name.
                    data[0] = -distance
            adj = {
                a for sr in examined
                for b in borders(sr)
                for a in territory_parts(territory(b))
            }
            examined |= adj
            distance += 1

        autodisbands.update((gvt, u['subregion'])
                            for _, _, _, u in sorted(unit_distances)[:abs(count)])

    new_units = []
    for u in units:
        if (u['government'], u['subregion']) in autodisbands:
            orders[territory(u['subregion'])] = {
                'user_issued': False, 'government': u['government'],
                'actor': u['subregion'],
                'action': 'D', 'result': 'D',
                'assist': None, 'target': None,
                'via_convoy': False, 'convoy': False
            }
        else:
            new_units.append(u)

    return new_units

def update_ownership(units, owns):
    current = {o['territory']: o for o in owns}
    current.update(
        (territory(u['subregion']),
         {'territory': territory(u['subregion']), 'government': u['government']})
        for u in units
        if u['u_type'] == 'A'
    )

    return list(current.itervalues())

def increment_turn(turn):
    number = turn['number'] + 1
    return {
        'number': number,
        'year': 1900 + number // len(standard.seasons),
        'season': standard.seasons[number % len(standard.seasons)],
    }

def generate(turn, orders, units, owns):
    if turn['season'] in ('S', 'F'):
        dependencies = construct_dependencies(orders)
        paradox_convoys = detect_paradox(orders, dependencies)
        fails = immediate_fails(orders, units)
        decisions = resolve((), orders, dependencies, fails, paradox_convoys, units)
    elif turn['season'] in ('SR', 'FR'):
        decisions = resolve_retreats(orders)
    else:
        decisions = resolve_adjusts(orders)

    # Mark the orders with the decisions from the resolver, 'S' for success, 'F' for failure
    for T, d in decisions:
        orders[T]['result'] = ('S' if d else 'F')

    # Update the units so that the previous pointer will point to the correct place
    for u in units:
        u['previous'] = u['subregion']

    if turn['season'] in ('SR', 'FR'):
        units = update_retreats(orders, units)

    if turn['season'] in ('S', 'F'):
        units = update_movements(orders, units)

    if turn['season'] == 'FA':
        units = update_adjusts(orders, units)
        units = update_autodisbands(orders, units, owns)

    turn = increment_turn(turn)

    if turn['season'] == 'FA':
        owns = update_ownership(units, owns)

    return turn, orders, units, owns

def initialize_game():
    turn = {
        'number': 0,
        'year': 1900,
        'season': standard.seasons[0],
    }

    units = [
        {'government': government,
         'u_type': convert[unit[1]],
         'subregion': (T, unit[0], unit[1])}
        for T, (government, sc, unit) in standard.definition.iteritems()
        if unit
    ]

    owns = [
        {'territory': T,
         'government': government,
         'is_supply': sc}
        for T, (government, sc, unit) in standard.definition.iteritems()
        if government
    ]

    return turn, units, owns
