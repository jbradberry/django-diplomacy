from . import standard
from .main import find_convoys, builds_available
from .utils import unit_in, territory, borders, territory_parts


def valid_hold(actor, units, owns, season):
    if season in ('S', 'F'):
        if unit_in(actor, units):
            return {None: {None: False}}
    return {}


def valid_move(actor, units, owns, season):
    if season == 'FA':
        return {}

    actor_set = [u for u in units if territory(u['subregion']) == territory(actor)]

    target = borders(actor)

    if season in ('SR', 'FR'):
        # only dislodged units retreat
        actor_set = [a for a in actor_set if a['dislodged']]

        target = [
            t for t in target
            # only go to empty territories ...
            if not any(territory(e['subregion']) == territory(t) for e in units)
            # that weren't the source of a displacing attack ...
            and all(territory(t) != a['displaced_from'] for a in actor_set)
            # and that isn't empty because of a standoff.
            and all(territory(t) != u['standoff_from'] for u in units)
        ]

    if len(actor_set) != 1:
        return {}

    convoyable = set()
    # Is the unit a convoyable army?  If so, include places it can convoy to.
    if season in ('S', 'F') and any(a['u_type'] == 'A' for a in actor_set):
        target = set(target)
        fleets = [
            u['subregion'] for u in units
            if u['u_type'] == 'F'
            and not any(p[2] == 'L' for p in territory_parts(territory(u['subregion'])))
        ]
        for fset, lset in find_convoys(units, fleets):
            if actor in lset:
                target.update(lset)
                convoyable.update(lset)
        target.discard(actor)

    if not target:
        return {}
    return {
        None: {x: (x in convoyable
                   and any(x == b for b in borders(actor)))
               for x in target}
    }


def valid_support(actor, units, owns, season):
    if season not in ('S', 'F'):
        return {}

    if not unit_in(actor, units):
        return {}

    adj = {sr for b in borders(actor)
           for sr in territory_parts(territory(b))}

    # support to hold
    results = {
        a: {None: False} for a in adj
        if unit_in(a, units)
    }

    # support to attack
    attackers = {
        b for a in adj
        for b in borders(a)
        if b != actor
        and unit_in(b, units)
    }
    for a in attackers:
        reachable = adj & set(borders(a))
        results.setdefault(a, {}).update((x, False) for x in reachable)

    # support to convoyed attack
    attackers = {
        u['subregion'] for u in units
        if u['u_type'] == 'A'
        and u['subregion'] != actor
    }
    fleets = [
        u['subregion'] for u in units
        if u['u_type'] == 'F'
        and not any(p[2] == 'L' for p in territory_parts(u['subregion']))
        and u['subregion'] != actor  # if we are issuing a support, we can't convoy.
    ]
    for fset, lset in find_convoys(units, fleets):
        for a in attackers:
            if a not in lset:
                continue
            if not (adj & lset - {a}):
                continue
            results.setdefault(a, {}).update(
                (x, False) for x in (adj & lset - {a})
            )

    return results


def valid_convoy(actor, units, owns, season):
    if season not in ('S', 'F'):
        return {}

    if not unit_in(actor, units):
        return {}
    if actor[2] != 'S':
        return {}

    fleets = [
        u['subregion'] for u in units
        if u['u_type'] == 'F'
        and not any(p[2] == 'L' for p in territory_parts(territory(u['subregion'])))
    ]

    for fset, lset in find_convoys(units, fleets):
        if actor in fset:
            attackers = {
                u['subregion'] for u in units
                if u['u_type'] == 'A'
                and u['subregion'] in lset
            }
            return {a: {x: False for x in lset - {a}}
                    for a in attackers}
    return {}


def valid_build(actor, units, owns, season):
    if not season == 'FA':
        return {}

    owns_index = {o['territory']: o for o in owns}
    current_government = owns_index.get(territory(actor), {}).get('government')
    home_government, is_supply = '', False
    if territory(actor) in standard.starting_state:
        home_government, is_supply, _ = standard.starting_state[territory(actor)]

    # It has to be a supply center and the current government has to have builds available.
    if not (is_supply and builds_available(units, owns).get(current_government, 0) > 0):
        return {}
    # Only can build if the territory is currently unoccupied.
    if any(territory(u['subregion']) == territory(actor) for u in units):
        return {}
    # And only if the territory is one of this government's "home" territories.
    if current_government == home_government:
        return {None: {None: False}}
    return {}


def valid_disband(actor, units, owns, season):
    if season in ('S', 'F'):
        return {}

    unit = [u for u in units if territory(u['subregion']) == territory(actor)]
    if season in ('SR', 'FR'):
        if not any(u['dislodged'] for u in unit):
            return {}
    elif builds_available(units, owns).get(unit[0]['government'], 0) >= 0:
        return {}
    return {None: {None: False}}


def is_legal(order, units, owns, season):
    builds = builds_available(units, owns)

    if order['actor'] is None:
        if season != 'FA':
            return False
        unit = ()
    else:
        unit = [u for u in units if u['subregion'] == order['actor']]

    if order['actor'] is None or order['action'] is None:
        return (season == 'FA' and
                builds.get(order['government'], 0) > 0)
    if order['action'] != 'B' and not unit:
        return False

    if season in ('S', 'F'):
        if unit[0]['government'] != order['government']:
            return False
    elif season in ('SR', 'FR'):
        unit = [u for u in unit if u['dislodged']]
        if not unit:
            return False
        if unit[0]['government'] != order['government']:
            return False
    elif order['action'] == 'D':
        if unit and unit[0]['government'] != order['government']:
            return False
    elif order['action'] == 'B':
        if not any(o['territory'] == territory(order['actor'])
                   and o['government'] == order['government']
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
