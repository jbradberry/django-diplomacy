from django.forms.models import ModelForm, BaseModelFormSet
from django.forms.fields import ChoiceField
from django.forms.util import ValidationError
from diplomacy.models import Order, Subregion, Unit

def validtree(game, gvt):
    season = game.current_turn().season
    convert = {'L': 'A', 'S': 'F'}
    tree = {}

    sr = Subregion.objects.all()
    if season == 'FB' and gvt.builds_available() > 0:
        actor = sr.filter(territory__power__government=gvt,
                          territory__government=gvt,
                          territory__is_supply=True).exclude(
            territory__subregion__unit__government__game=game)
    else:
        if season in ('SR', 'FR'):
            actor = sr.filter(unit__government=gvt,
                              unit__displaced_from__isnull=False)
        else:
            actor = sr.filter(unit__government=gvt)

    for i in actor:
        lvl1 = tree.setdefault(convert[i.sr_type], {})
        lvl2 = lvl1.setdefault(i.id, {})
        for j in ('H', 'M', 'S', 'C', 'B', 'D'):
            if season in ('S', 'F') and j in ('B', 'D'):
                continue
            if season in ('SR', 'FR') and j not in ('M', 'D'):
                continue
            if season == 'FB':
                if j not in ('B', 'D'):
                    continue
                if j == 'B' and gvt.builds_available() <= 0:
                    continue
                if j == 'D' and gvt.builds_available() >= 0:
                    continue
            else:
                unit = Unit.objects.get(government=gvt, subregion=i)
            
            if j in ('H', 'B', 'D'):
                target, dest = [u''], [u'']
            if j in ('M', 'S'):
                dest = [u'']

            if j == 'M':
                target = sr.filter(borders=i)
                if season in ('SR', 'FR'):
                    target = target.exclude(
                        unit__government__game=game).exclude(
                        territory=unit.displaced_from).exclude(
                        territory__standoff__government__game=game)
                target = target.values_list('id', flat=True)
                if not target:
                    continue
                if season in ('S', 'F') and unit.u_type == 'A':
                    coastal = sr.filter(sr_type='L',
                                        territory__subregion__sr_type='S'
                                        ).values_list('id', flat=True)
                    if i.id in coastal:
                        target = list(set(list(target) + list(coastal)))
                        target.remove(i.id)
                        target.sort()
            if j == 'S':
                target = sr.filter(
                    unit__government__game=game
                    ).exclude(id=i.id).values_list('id', flat=True)
                dest += list(sr.filter(borders=i
                                       ).values_list('id', flat=True))
            if j == 'C':
                if unit.u_type != 'F':
                    continue
                coastal = sr.filter(sr_type='L',
                                    territory__subregion__sr_type='S'
                                    ).distinct()
                target = coastal.filter(unit__government__game=game
                                        ).values_list('id', flat=True)
                dest = coastal.values_list('id', flat=True)

            lvl2.update({j: (list(target), list(dest))})

    return tree

class OrderForm(ModelForm):
    class Meta:
        model = Order
        exclude = ('turn', 'government')
        
    def __init__(self, game, government, sr, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.game = game
        self.government = government
        self.season = game.current_turn().season

        my_css = {'u_type': 'u_type',
                  'actor': 'subregion',
                  'action': 'action',
                  'target': 'subregion',
                  'destination': 'subregion'}
        for w, c in my_css.items():
            self.fields[w].widget.attrs['class'] = c

class OrderFormSet(BaseModelFormSet):
    def __init__(self, game, government, data=None, queryset=None, **kwargs):
        self.game = game
        self.government = government
        self.sr = Subregion.objects.select_related('territory__name').all()
        self.names = dict((i.pk, unicode(i)) for i in self.sr)
        super(OrderFormSet, self).__init__(data=data,
                                           queryset=queryset, **kwargs)

    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, game=self.game,
                                                   government=self.government,
                                                   names=self.names,
                                                   sr=self.sr,))
