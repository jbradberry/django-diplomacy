from collections import defaultdict
import re

from .. import models


convert = {'F': 'S', 'A': 'L'}
other = {'L': 'S', 'S': 'L', 'F': 'A', 'A': 'F'}

location = (r"(?{territory}[-\w.]{{2,}}(?: [-\w.]{{2,}})*)"
            r"(?: \((?{subname}\w+)\))?")
unit = r"(?{u_type}F|A) " + location
locRE = re.compile(location.format(territory="P<territory>",
                                   subname="P<subname>"))
unitRE = re.compile(unit.format(u_type="P<u_type>",
                                territory="P<territory>",
                                subname="P<subname>"))
unit_enhRE = re.compile(unit.format(u_type="P<u_type>",
                                    territory="P<territory>",
                                    subname="P<subname>") +
                        r"(?:, (displaced_from=[-\w.]+(?: [-\w.]+)*))?" +
                        r"(?:, (standoff_from=[-\w.]+(?: [-\w.]+)*))?")
opts = {'u_type': ':', 'territory': ':', 'subname': ':'}
U, L = unit.format(**opts), location.format(**opts)
order_patterns = {'H': re.compile(r"(?P<actor>{0}) H$".format(U)),
                  'M': re.compile(r"(?P<actor>{0}) M"
                                  r" (?P<target>{1})"
                                  r"(?: (?P<via_convoy>[*]))?$".format(U, L)),
                  'S': re.compile(r"(?P<actor>{0}) S (?P<assist>{0})"
                                  r"(?: - (?P<target>{1}))?$".format(U, L)),
                  'C': re.compile(r"(?P<actor>{0}) C (?P<assist>{0})"
                                  r" - (?P<target>{1})$".format(U, L)),
                  'B': re.compile(r"(?P<actor>{0}) B$".format(U)),
                  'D': re.compile(r"(?P<actor>{0}) D$".format(U))}

lookup = defaultdict(list)
for t in models.Territory.objects.all():
    for sr in t.subregion_set.all():
        lookup[(t.name,)].append(sr)
        lookup[(t.name, sr.subname or '')].append(sr)
        lookup[(t.name, sr.subname or '', sr.sr_type)].append(sr)

t_dict = dict((t.name, t.id) for t in models.Territory.objects.all())


def fetch(sr_type, territory, subname, strict=False):
    if sr_type in ('F', 'A'):
        sr_type = convert[sr_type]
    if subname is None:
        subname = ''
    if not lookup[(territory,)]:
        return
    if subname != '':
        if not lookup[(territory, subname)]:
            subname = ''

    result = lookup[(territory, subname, sr_type)]
    if not result and not strict:
        result = lookup[(territory, subname, other[sr_type])]
    if len(result) == 1:
        return result[0]

def create_unit(turn, gvt, unitstr):
    u = unit_enhRE.match(unitstr)
    kwargs = (group.split('=') for group in u.groups('') if '=' in group)
    kwargs = dict((g[0], territory[g[1]]) for g in kwargs)
    opts = u.groupdict('')
    return models.Unit.objects.create(u_type=opts['u_type'],
                                      subregion=fetch(opts['u_type'],
                                                      opts['territory'],
                                                      opts['subname']),
                                      turn=turn, government=gvt,
                                      **kwargs)

def create_units(units, turn):
    for gname, uset in units.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        for unit in uset:
            create_unit(turn, gvt, unit)

def split_unit(ustr, regexp=None):
    if regexp is None:
        regexp = unitRE
    u = regexp.match(ustr)
    if not u:
        return ('', '', '')
    return u.groups('')

def create_order(turn, gvt, orderstr):
    for action, regexp in order_patterns.iteritems():
        o = regexp.match(orderstr)
        if o is not None:
            break
    o_dict = o.groupdict('')
    actor = fetch(*split_unit(o_dict.get('actor', '')),
                   strict=(turn.season == 'FA'))
    assist = fetch(*split_unit(o_dict.get('assist', '')))
    sr_type = assist.sr_type if assist else (actor.sr_type if actor else '')
    target = fetch(sr_type, *split_unit(o_dict.get('target', ''), locRE)[:2])

    kwargs = {'actor': actor, 'action': action,
              'assist': assist, 'target': target,
              'via_convoy': bool(o_dict.get('via_convoy'))}

    return models.Order.objects.create(turn=turn, government=gvt, **kwargs)

def create_orders(orders, turn):
    for gname, oset in orders.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        new_orders = [create_order(turn, gvt, order) for order in oset]
        if turn.season == 'FA':
            for i, o in enumerate(sorted(new_orders, key=lambda x: x.actor_id)):
                o.slot = i
                o.save()
