from collections import defaultdict

from . import standard
from .check import is_legal
from .compare import assist, construct_dependencies
from .digest import actionable_subregions, builds_available
from .resolver import (detect_paradox, immediate_fails, resolve, resolve_retreats,
                       resolve_adjusts)
from .utils import (convert, get_territory, borders, territory_parts,
                    has_land, is_land, is_sea, is_army, is_fleet)


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
        if has_land(u['subregion'])
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
