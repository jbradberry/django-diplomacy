from . import standard


convert = {'L': 'A', 'S': 'F'}


def get_territory(sr_token):
    if not sr_token:
        return u''
    return sr_token.split(u'.')[0]


def territory_parts(t_token):
    return standard.subregion_groups.get(t_token, ())


def borders(sr_token):
    return standard.connectivity.get(sr_token, ())


def unit_in(sr_token, units):
    return any(u['subregion'] == sr_token for u in units)


def territory_display(t_token):
    return standard.territories.get(t_token, u'')


def subregion_display(sr_token):
    if sr_token not in standard.subregions:
        return u''
    T, subname, sr_type = standard.subregions[sr_token]
    return u"{} ({})".format(T, subname) if subname else T


def unit_display(sr_token):
    if sr_token not in standard.subregions:
        return u''
    T, subname, sr_type = standard.subregions[sr_token]
    base = u"{} {}".format(convert[sr_type], T)
    return u"{} ({})".format(base, subname) if subname else base


def power_token(p_str):
    return standard.inv_powers.get(p_str, u'')


def territory_token(t_str):
    return standard.inv_territories.get(t_str, u'')


def subregion_token(sr_tuple):
    return standard.inv_subregions.get(sr_tuple, u'')


def is_land(sr_token):
    return sr_token.endswith('.l')


def is_sea(sr_token):
    return sr_token.endswith('.s')


def has_land(sr_token):
    return any(is_land(sr) for sr in territory_parts(get_territory(sr_token)))


def has_sea(sr_token):
    return any(is_sea(sr) for sr in territory_parts(get_territory(sr_token)))


is_army = is_land


is_fleet = is_sea
