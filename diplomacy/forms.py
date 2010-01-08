from django.forms.models import ModelForm, BaseModelFormSet
from django.forms.fields import ChoiceField
from django.forms import ValidationError
from diplomacy.models import Order, Subregion, Unit

def validtree(game, gvt):
    season = game.current_turn().season
    convert = {'L': 'A', 'S': 'F'}
    tree = {}

    sr = Subregion.objects.all()
    if season == 'FA' and gvt.builds_available() > 0:
        tree[''] = {'': {'B': ([u''], [u''])}}
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
            if season == 'FA':
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
        
    def __init__(self, game, government, *args, **kwargs):
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

    def clean(self):
        cleaned_data = self.cleaned_data
        tree = validtree(self.game, self.government)
        u_type = cleaned_data.get("u_type")
        actor = cleaned_data.get("actor")
        actor = actor.id if actor else ""
        action = cleaned_data.get("action")
        target = cleaned_data.get("target")
        target = target.id if target else ""
        dest = cleaned_data.get("destination")
        dest = dest.id if dest else ""

        if self.season != 'FA':
            u, a = self.initial['u_type'], self.initial['actor']
            if u_type != u or actor != a:
                raise ValidationError("You may not change the acting unit.")

        try:
            T, D = tree[u_type][actor][action]
            if target not in T or dest not in D:
                raise ValidationError("Invalid order.")
        except KeyError:
            raise ValidationError("Invalid order.")

        return cleaned_data

class OrderFormSet(BaseModelFormSet):
    def __init__(self, game, government, data=None, queryset=None, **kwargs):
        self.game = game
        self.government = government
        super(OrderFormSet, self).__init__(data=data,
                                           queryset=queryset, **kwargs)

    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, game=self.game,
                                                   government=self.government))

    def clean(self):
        if any(self.errors):
            return

        if self.total_form_count() > self.initial_form_count():
            raise ValidationError("You may not add orders.")
        if self.total_form_count() < self.initial_form_count():
            raise ValidationError("You may not delete orders.")

        actors = []
        for i in range(self.total_form_count()):
            form = self.forms[i]
            actor = form.cleaned_data["actor"].territory
            if not actor:
                continue
            if actor in actors:
                raise ValidationError(
                    "You may not give a territory multiple orders.")
            actors.append(actor)

        if self.game.current_turn().season == 'FA':
            builds = self.government.builds_available()
            if builds >= 0:
                if len(actors) > builds:
                    raise ValidationError("You may not build more units than you have supply centers.")
            if builds < 0:
                if len(actors) != abs(builds):
                    u = "unit" if builds == -1 else "units"
                    msg = "You must disband exactly %d %s." % (abs(builds), u)
                    raise ValidationError(msg)
