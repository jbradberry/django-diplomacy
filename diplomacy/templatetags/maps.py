from ..models import Territory, Power
from django import template
import json
import re

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
        data['owns'] = json.dumps(
            [(re.sub('[ .]', '', T.name.lower()), G.power.name)
             for G in game.government_set.all()
             for T in Territory.objects.filter(ownership__turn=turn,
                                               ownership__government=G)])
        data['units'] = json.dumps(
            [(unicode(u.subregion), u.u_type, u.government.power.name)
             for u in turn.unit_set.filter(dislodged=False)])
    else:
        data['owns'] = json.dumps(
            [(re.sub('[ .]', '', T.name.lower()), P.name)
             for P in Power.objects.all()
             for T in Territory.objects.filter(power=P)])
        data['units'] = json.dumps([])
    return data
