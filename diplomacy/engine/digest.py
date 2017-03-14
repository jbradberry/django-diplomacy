from collections import defaultdict, Counter
from itertools import combinations

from . import standard
from .utils import get_territory, borders, territory_parts, has_land, is_land


def find_convoys(units, fleets):
    """
    Generates pairs consisting of a cluster of adjacent non-coastal
    fleets, and the coastal territories that are reachable via convoy
    from that cluster.  This is necessary to determine legal orders.

    """
    fleets = [f for f in fleets if not has_land(f)]
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
            for sr in territory_parts(get_territory(b))
            if is_land(sr)
        }
        if coasts & armies:
            convoyable.append((set(gset), coasts))

    return convoyable


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
                occupied = {get_territory(u['subregion']) for u in units}
                actors_index[government] = [
                    sr for T in owned_sc
                    for sr in territory_parts(T)
                    if standard.starting_state[T][0] == government
                    and T not in occupied
                ]
            elif builds.get(government, 0) == 0:
                actors_index[government] = []
            else:
                actors_index[government] = [u['subregion'] for u in units
                                            if u['government'] == government]

        return actors_index
    return {}
