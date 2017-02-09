import json
import re

from django import template

from ..engine import standard
from ..engine.utils import territory


register = template.Library()

colors = {'Austria-Hungary': '#a41a10',
          'England': '#1010a3',
          'France': '#126dc0',
          'Germany': '#5d5d5d',
          'Italy': '#30a310',
          'Russia': '#7110a2',
          'Turkey': '#e6e617'}


@register.inclusion_tag('diplomacy/map_card.html', takes_context=True)
def map(context, width, height):
    game = context['game']
    turn = context.get('turn', game.current_turn())
    data = {'width': width, 'height': height}

    data['colors'] = json.dumps(colors)
    if turn:
        units = turn.get_units()
        owns = turn.get_ownership()

        data['owns'] = json.dumps(
            [(re.sub('[ .]', '', o['territory'].lower()), o['government'])
             for o in owns]
        )
        data['units'] = json.dumps(
            [("{}{}".format(territory(u['subregion']),
                            " ({})".format(u['subregion'][1]) if u['subregion'][1] else ''),
              u['u_type'], u['government'])
             for u in units
             if not u['dislodged']])
    else:
        data['owns'] = json.dumps(
            [(re.sub('[ .]', '', T.lower()), P)
             for P in standard.powers
             for T, (p, sc, unit) in standard.definition.iteritems()
             if p == P])
        data['units'] = json.dumps([])
    return data
