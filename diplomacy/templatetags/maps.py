import json

from django import template

from ..engine import standard
from ..engine.utils import subregion_display


register = template.Library()

colors = {'austria-hungary': '#a41a10',
          'england': '#1010a3',
          'france': '#126dc0',
          'germany': '#5d5d5d',
          'italy': '#30a310',
          'russia': '#7110a2',
          'turkey': '#e6e617'}


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
            [(o['territory'], o['government']) for o in owns]
        )
        data['units'] = json.dumps(
            [(subregion_display(u['subregion']), u['u_type'], u['government'])
             for u in units
             if not u['dislodged']]
        )
    else:
        data['owns'] = json.dumps(
            [(T, P)
             for P in standard.powers
             for T, (p, sc, unit) in standard.starting_state.items()
             if p == P])
        data['units'] = json.dumps([])
    return data
