from . import standard


convert = {'L': 'A', 'S': 'F'}


def territory(sr_token):
    if not sr_token:
        return u''
    return sr_token.split(u'.')[0]


def territory_parts(t_token):
    return standard.subregion_groups.get(t_token, ())


def borders(sr_token):
    return standard.connectivity.get(sr_token, ())


def unit_in(sr_token, units):
    return any(u['subregion'] == sr_token for u in units)


def subregion_display(sr_token):
    if sr_token not in standard.subregions:
        return u''
    T, subname, sr_type = standard.subregions[sr_token]
    return u"{} ({})".format(T, subname) if subname else T
