from diplomacy.models import Territory
from django import template
from django.utils import simplejson
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
    data['MEDIA_URL'] = context['MEDIA_URL']
    data['colors'] = simplejson.dumps(colors)
    data['owns'] = simplejson.dumps(
        [(re.sub('[ .]', '', T.name.lower()), G.power.name)
         for G in game.government_set.all()
         for T in Territory.objects.filter(ownership__turn=turn,
                                           ownership__government=G)])
    data['units'] = simplejson.dumps(
        [(unicode(u.subregion), u.u_type, u.government.power.name)
         for u in turn.unit_set.filter(displaced_from__isnull=True)])
    return data
