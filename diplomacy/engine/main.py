from collections import defaultdict

from . import standard
from .check import is_legal
from .compare import assist, head_to_head, construct_dependencies
from .digest import find_convoys, actionable_subregions, builds_available
from .utils import (convert, get_territory, borders, territory_parts,
                    is_land, is_sea, is_army, is_fleet)


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
            assist = orders[get_territory(o['assist'])]
            if o['target']:
                if (assist['action'] == 'M' and
                    assist['target'] == o['target']):
                    continue
            else:
                if assist['action'] in ('H', 'C', 'S'):
                    continue
        results.add(T)

    return results

def calculate_paths(state, orders, paradox, units):
    """Determine if moves have a valid path."""

    # True if this unit is successfully convoyed, False otherwise.
    convoy = defaultdict(lambda: False)

    path = {}
    for T, order in orders.iteritems():
        if order['action'] == 'M':
            path[T], P = False, False

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

    return path, convoy

def calculate_base_strengths(state, orders, unit_index, path, convoy):
    """Calculate base hold, attack, and prevent strengths."""

    # The hold strength is defined for an area, not a unit.  It is the defensive
    # strength of an area when a unit declines to move, or fails in its ordered
    # movement.  Attacks have to overcome this strength.
    hold_str = defaultdict(int)

    # The strength of an attack, complicated by the rules about paths and nationality.
    attack_str = defaultdict(int)

    # In cases where there is a head-to-head battle, the unit has to overcome the
    # power of the move of the opposing unit.  All movements have a head-to-head
    # attack strength of at least 1.
    defend_str = defaultdict(int)

    # The strength of competing attacks into a territory.
    prevent_str = defaultdict(int)

    for T, order in orders.iteritems():
        if order['action'] == 'M':
            defend_str[T] = 1
            if path[T]:
                prevent_str[T], attack_str[T] = 1, 1

                if get_territory(order['target']) in state:
                    T2 = get_territory(order['target'])
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

    return hold_str, attack_str, defend_str, prevent_str

def calculate_supports(state, orders, unit_index, hold_str, attack_str, defend_str,
                       prevent_str, convoy):
    """Calculate additions to strengths due to support orders."""
    for T, d in state.iteritems():
        order = orders[T]

        if not d or order['action'] != 'S':
            continue

        if not order['target']:
            hold_str[get_territory(order['assist'])] += 1
        else:
            if attack_str[get_territory(order['assist'])]:
                T2 = get_territory(order['target'])
                d2 = state.get(T2, False)
                if T2 not in orders:
                    attack_str[get_territory(order['assist'])] += 1
                elif (d2
                      and orders[T2]['action'] == 'M'
                      and not head_to_head(T, order, T2, orders[T2],
                                           convoy[T], convoy[T2])):
                    attack_str[get_territory(order['assist'])] += 1
                # other unit is not ours
                elif unit_index[T]['government'] != unit_index[T2]['government']:
                    attack_str[get_territory(order['assist'])] += 1
            if defend_str[get_territory(order['assist'])]:
                defend_str[get_territory(order['assist'])] += 1
            if prevent_str[get_territory(order['assist'])]:
                prevent_str[get_territory(order['assist'])] += 1

def consistent_move(T, d, orders, fails, hold_str, attack_str, defend_str, prevent_str,
                    path, convoy):
    order = orders[T]
    target = get_territory(order['target'])
    move = True
    # Fail in a head-to-head attack
    if (target in orders
        and head_to_head(T, order, target, orders[target],
                         convoy[T], convoy[target])
        and attack_str[T] <= defend_str[target]):
        move = False
    # Fail in a standard attack
    if attack_str[T] <= hold_str[target]:
        move = False
    # Fail in a competing attack
    if any(attack_str[T] <= prevent_str[T2]
           for T2, o2 in orders.iteritems()
           if T != T2 and o2['action'] == 'M'
           and get_territory(o2['target']) == target):
        move = False
    # Path to move does not exist
    if not path[T]:
        move = False
    # Or the move was observed to be a failure initially
    if T in fails:
        move = False

    # If the assumed outcome in `state` does not match any of the above, the
    # state is inconsistent.
    if d ^ move:
        return False

    return True

def consistent_support(T, d, orders, fails, hold_str, attack_str):
    order = orders[T]
    target = get_territory(order['target'])
    attackers = set(T2 for T2, o2 in orders.iteritems()
                    if o2['action'] == 'M'
                    and get_territory(o2['target']) == T)
    # Is the support cut?
    cut = (T in fails
           or (target in attackers
               and attack_str[target] > hold_str[T])
           or any(attack_str[T2] > 0 for T2 in attackers
                  if T2 != target))

    # The value in `state` must match the calculation of whether the support
    # was cut or not.
    if d ^ (not cut):
        return False

    return True

def consistent_hold(T, d, orders, fails, hold_str, attack_str, prevent_str):
    hold = True
    # The order was initially observed to be a failure.
    if T in fails:
        hold = False

    attackers = set(T2 for T2, o2 in orders.iteritems()
                    if o2['action'] == 'M'
                    and get_territory(o2['target']) == T)
    # Is there enough to dislodge this unit?
    if attackers:
        S, P, A = max((attack_str[T2], prevent_str[T2], T2)
                      for T2 in attackers)
        if S > hold_str[T] and not any(prevent_str[T2] >= S
                                       for T2 in attackers
                                       if T2 != A):
            hold = False

    # Whether or not the unit is calculated to be dislodged must match the
    # assumed value in `state`, with the exception of a convoy paradox
    # (stored in `state` as None).
    if (d is not False) ^ hold:
        return False

    return True

def consistent(state, orders, fails, paradox, units):
    state = dict(state)
    unit_index = {get_territory(u['subregion']): u for u in units}

    path, convoy = calculate_paths(state, orders, paradox, units)
    hold_str, attack_str, defend_str, prevent_str = calculate_base_strengths(
        state, orders, unit_index, path, convoy)
    calculate_supports(state, orders, unit_index, hold_str, attack_str, defend_str,
                       prevent_str, convoy)

    # determine if the strength calculations are consistent with the state
    for T, d in state.iteritems():
        order = orders[T]
        if order['action'] == 'M':
            if not consistent_move(T, d, orders, fails, hold_str, attack_str, defend_str,
                                   prevent_str, path, convoy):
                return False

        if order['action'] == 'S':
            if not consistent_support(T, d, orders, fails, hold_str, attack_str):
                return False

        if order['action'] in ('H', 'C'):
            if not consistent_hold(T, d, orders, fails, hold_str, attack_str,
                                   prevent_str):
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
            target_count[get_territory(order['target'])] += 1
        else:
            decisions.append((T, None))
    for T, order in orders.iteritems():
        if order['action'] != 'M':
            continue
        if target_count[get_territory(order['target'])] == 1:
            decisions.append((T, True))
        else:
            decisions.append((T, False))
    return decisions

def resolve_adjusts(orders):
    return [(T, bool(order.get('action')))
            for T, order in orders.iteritems()]

def normalize_orders(turn, orders, units, owns):
    """Returns a list of order dicts, taken from the orders previously
    submitted this turn, filtered down by legality and refilled with
    defaults.  This list is exhaustive, no units not covered by the
    list or number of builds in excess will be permitted.

    """
    actors = actionable_subregions(turn, units, owns)

    # Construct the set of default orders.  This will be the fully constrained set.
    if turn['season'] == 'FA':
        builds = builds_available(units, owns)
        orders_index = {
            (government, index): {
                'government': government, 'actor': '',
                'action': '', 'assist': '', 'target': '',
                'via_convoy': False, 'convoy': False, 'user_issued': False
            }
            for government, B in builds.iteritems()
            for index in xrange(-B if B < 0 else min(B, len(actors.get(government, ()))))
        }
    else:
        action = 'H' if turn['season'] in ('S', 'F') else ''
        orders_index = {
            (government, a): {
                'government': government, 'actor': a,
                'action': action, 'assist': '', 'target': '',
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
            if o['action'] != 'M' or not is_land(o['actor']):
                continue

            # Find all of the convoy orders that match the current move,
            # both overall and specifically by this user's government.
            matching = [
                (g2, o2) for (g2, i2), o2 in orders_index.iteritems()
                if o2['action'] == 'C'
                and assist(get_territory(o['actor']), o, get_territory(o2['actor']), o2)
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
        T = get_territory(u['subregion'])
        if T not in orders or not u['dislodged']:
            new_units.append(u)
            continue

        order = orders[T]
        if not order['action']:
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
        T = get_territory(u['subregion'])
        order = orders[T]
        if order['action'] == 'M':
            if order['result'] == 'S':
                u['subregion'] = order['target']
                # if the move succeeded, any unit occupying the target
                # territory will be displaced
                displaced[get_territory(order['target'])] = T
            else:
                failed[get_territory(order['target'])] += 1

    for u in units:
        T = get_territory(u['previous'])
        order = orders[T]
        if T in displaced and not (order['action'] == 'M' and order['result'] == 'S'):
            order['result'] = 'B'
            u.update(
                dislodged=True,
                # only mark a location as disallowed for retreats if it
                # wasn't via convoy.
                displaced_from=(
                    '' if orders[displaced[T]].get('convoy') else displaced[T])
            )

        target = get_territory(order['target'])
        # if multiple moves to our target failed, we have a standoff
        if order['action'] == 'M' and failed[target] > 1:
            u['standoff_from'] = target

    return units

def update_adjusts(orders, units):
    new_units = []
    for u in units:
        T = get_territory(u['subregion'])
        order = orders.get(T, {})
        if order.get('action') == 'D':
            order['result'] = 'D'
        else:
            new_units.append(u)

    for T, o in orders.iteritems():
        if o['action'] == 'B' and o['result'] == 'S':
            new_units.append({
                'government': o['government'],
                'u_type': 'A' if is_army(o['actor']) else 'F',
                'subregion': o['actor'],
                'previous': '',
                'dislodged': False,
                'displaced_from': '',
                'standoff_from': '',
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
            [None, is_army(u['subregion']), get_territory(u['subregion']), u]
            for u in units
            if u['government'] == gvt
        ]

        distance = 0
        examined = {
            sr for T, (power, sc, _) in standard.starting_state.iteritems()
            for sr in territory_parts(T)
            if is_sea(sr) and sc
            and power == gvt
        }
        while any(is_fleet(u['subregion']) and D is None
                  for D, _, _, u in unit_distances):
            for data in unit_distances:
                D, _, _, u = data
                if is_fleet(u['subregion']) and D is None and u['subregion'] in examined:
                    # We want them reversed by distance, but non-reversed by name.
                    data[0] = -distance
            adj = {b for sr in examined for b in borders(sr)}
            examined |= adj
            distance += 1

        distance = 0
        examined = {
            sr for T, (power, sc, _) in standard.starting_state.iteritems()
            for sr in territory_parts(T)
            if sc and power == gvt
        }
        while any(is_army(u['subregion']) and D is None
                  for D, _, _, u in unit_distances):
            for data in unit_distances:
                D, _, _, u = data
                if is_army(u['subregion']) and D is None and u['subregion'] in examined:
                    # We want them reversed by distance, but non-reversed by name.
                    data[0] = -distance
            adj = {
                a for sr in examined
                for b in borders(sr)
                for a in territory_parts(get_territory(b))
            }
            examined |= adj
            distance += 1

        autodisbands.update((gvt, u['subregion'])
                            for _, _, _, u in sorted(unit_distances)[:abs(count)])

    new_units = []
    for u in units:
        if (u['government'], u['subregion']) in autodisbands:
            orders[get_territory(u['subregion'])] = {
                'user_issued': False, 'government': u['government'],
                'actor': u['subregion'],
                'action': 'D', 'result': 'D',
                'assist': '', 'target': '',
                'via_convoy': False, 'convoy': False
            }
        else:
            new_units.append(u)

    return new_units

def update_ownership(units, owns):
    current = {o['territory']: o for o in owns}
    current.update(
        (get_territory(u['subregion']),
         {'territory': get_territory(u['subregion']), 'government': u['government']})
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
         'subregion': standard.inv_subregions[(standard.territories[T], unit[0], unit[1])]}
        for T, (government, sc, unit) in standard.starting_state.iteritems()
        if unit
    ]

    owns = [
        {'territory': T,
         'government': government,
         'is_supply': sc}
        for T, (government, sc, unit) in standard.starting_state.iteritems()
        if government
    ]

    return turn, units, owns
