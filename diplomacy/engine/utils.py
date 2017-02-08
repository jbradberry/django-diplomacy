from . import standard


convert = {'L': 'A', 'S': 'F'}


def territory(sr):
    if sr is None:
        return None
    return sr[0]


def territory_parts(t_key):
    return standard.territories.get(t_key, ())


def borders(sr_key):
    return standard.mapping.get(sr_key, ())


def unit_in(u_key, units):
    return any(u['subregion'] == u_key for u in units)
