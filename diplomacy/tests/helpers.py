from collections import defaultdict
import re

from .. import models
from ..engine import standard


convert = {u'F': u'S', u'A': u'L'}
other = {'L': 'S', 'S': 'L', 'F': 'A', 'A': 'F'}

location = (r"(?{territory}[-\w.]{{2,}}(?: [-\w.]{{2,}})*)"
            r"(?: \((?{subname}\w+)\))?")
unit = r"(?{u_type}F|A) " + location
locRE = re.compile(location.format(territory="P<territory>",
                                   subname="P<subname>"))
unitRE = re.compile(unit.format(u_type="P<sr_type>",
                                territory="P<territory>",
                                subname="P<subname>"))
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


subregion_index = defaultdict(list)
for sr_token, (territory, subname, sr_type) in standard.subregions.iteritems():
    subregion_index[(territory,)].append(sr_token)
    subregion_index[(territory, subname)].append(sr_token)
    subregion_index[(territory, subname, sr_type)].append(sr_token)


def get_subregion(territory, subname, sr_type, strict=False, **kwargs):
    sr_type = convert.get(sr_type, sr_type)
    subname = subname or u''
    if not subregion_index[(territory,)]:
        return u''
    if subname and not subregion_index[(territory, subname)]:
        subname = u''

    result = subregion_index[(territory, subname, sr_type)]
    if not result and not strict:
        result = subregion_index[(territory, subname, other[sr_type])]
    if len(result) == 1:
        return result[0]
    return u''

def parse(unitstr):
    unit = {}
    match = unitRE.match(unitstr)
    if match:
        unit.update(**match.groupdict(''))
    else:
        match = locRE.match(unitstr)
        if match:
            unit.update(**match.groupdict(''))
    return unit

def create_units(units, turn, governments):
    parsed = (
        (gvt, unitstr[0], parse(unitstr))
        for gvt, uset in units.iteritems()
        for unitstr in uset
    )
    return models.Unit.objects.bulk_create([
        models.Unit(turn=turn,
                    government=governments[gvt],
                    u_type=u_type,
                    subregion=get_subregion(udict.get('territory', ''),
                                            udict.get('subname', ''),
                                            udict.get('sr_type', '')))
        for gvt, u_type, udict in parsed
    ])

def create_orders(orders, turn, governments):
    order_posts = {
        gvt: models.OrderPost.objects.create(turn=turn, government=governments[gvt])
        for gvt in orders
    }

    parsed = (
        (gvt, action, regexp.match(orderstr))
        for gvt, oset in orders.iteritems()
        for orderstr in oset
        for action, regexp in order_patterns.iteritems()
    )
    parsed = (
        (gvt, action, omatch.groupdict(''))
        for gvt, action, omatch in parsed
        if omatch is not None
    )
    parsed = (
        (gvt, action,
         parse(odict.get('actor', '')),
         parse(odict.get('assist', '')),
         parse(odict.get('target', '')),
         bool(odict.get('via_convoy')))
        for gvt, action, odict in parsed
    )

    final_orders = [
        models.Order(post=order_posts[gvt],
                     actor=get_subregion(strict=(turn.season == 'FA'), **actor),
                     action=action,
                     assist=get_subregion(**assist) if assist else '',
                     target=get_subregion(
                         sr_type=assist.get('sr_type', '') if assist else actor.get('sr_type', ''),
                         **target
                     ) if target else '',
                     via_convoy=via_convoy)
        for gvt, action, actor, assist, target, via_convoy in parsed
    ]
    return models.Order.objects.bulk_create(final_orders)
