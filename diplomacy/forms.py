from django.forms.models import ModelForm, BaseFormSet, ModelChoiceField
from django.forms import ValidationError
from diplomacy.models import Order, Subregion, Unit

convert = {'L': 'A', 'S': 'F'}

def validorders(game, gvt):
    turn = game.current_turn()
    season = turn.season
    builds = gvt.builds_available()

    sr = Subregion.objects.all()
    coastal = sr.filter(sr_type='L',
                        territory__subregion__sr_type='S'
                        ).distinct() # required due to multiple coasts
    
    if season == 'FA' and builds > 0:
        actor = sr.filter(territory__power__government=gvt,
                          territory__ownership__turn=turn,
                          territory__ownership__government=gvt,
                          territory__is_supply=True).exclude(
            territory__subregion__unit__turn=turn)
    else:
        actor = sr.filter(unit__turn=turn,
                          unit__government=gvt)
        if season in ('SR', 'FR'):
            actor = actor.filter(unit__displaced_from__isnull=False)

    act = {'S': ('H', 'M', 'S', 'C'),
           'F': ('H', 'M', 'S', 'C'),
           'SR': ('M', 'D'),
           'FR': ('M', 'D'),
           'FA': ()}
    if season == 'FA' and builds != 0:
        act['FA'] = ('B',) if builds > 0 else ('D',)

    lvl0 = {}
    for a in actor:
        actions = act[season]
        lvl1 = {}
        for i in actions:
            if i in ('H', 'B', 'D'):
                assist, target = [u''], [u'']
            if i == 'M':
                assist, target = [u''], sr.filter(borders=a)
                if season in ('SR', 'FR'):
                    target = target.exclude(
                        unit__turn=turn).exclude(
                        territory=unit.displaced_from).exclude(
                        territory__standoff__unit__turn=turn)
                target = target.values_list('id', flat=True)
                if not target:
                    continue
                if season in ('S', 'F') and a in coastal:
                    target = list(set(target) |
                                  set(t.id for t in coastal))
                    target.remove(a.id)
            if i == 'S':
                assist = sr.filter(unit__turn=turn).exclude(
                    id=a.id).values_list('id', flat=True)
                target = [u''] + [t.id for t in sr.filter(borders=a)]
            if i == 'C':
                if a.sr_type == 'L' or sr.filter(territory=a.territory,
                                                 sr_type='L'):
                    continue
                assist = coastal.filter(unit__turn=turn
                                        ).values_list('id', flat=True)
                target = coastal.values_list('id', flat=True)

            lvl1.update({i: (list(assist), list(target))})

        lvl0.update({a.id: lvl1})

    if season == 'FA':
        tree = [lvl0 for i in xrange(abs(builds))]
    else:
        tree = [{a.id: lvl0[a.id]} for a in actor]

    return tree


class UnitProxyChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (convert[obj.sr_type], obj.territory.name)


class OrderForm(ModelForm):
    qs = Subregion.objects.select_related('territory__name').all()
    
    actor = UnitProxyChoiceField(queryset=qs, required=False)
    assist = UnitProxyChoiceField(queryset=qs, required=False)
    target = ModelChoiceField(queryset=qs, required=False)

    class Meta:
        model = Order
        exclude = ('turn', 'government', 'timestamp', 'slot')
        
    def __init__(self, slot, valid, season, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.slot, self.valid, self.season = slot, valid, season

        my_css = {'actor': 'subregion',
                  'action': 'action',
                  'assist': 'subregion',
                  'target': 'subregion',}
        for w, c in my_css.items():
            self.fields[w].widget.attrs['class'] = c

    def clean(self):
        cleaned_data = self.cleaned_data

        action = cleaned_data.get("action")
        actor = cleaned_data.get("actor")
        actor = actor.id if actor else ""
        assist = cleaned_data.get("assist")
        assist = assist.id if assist else ""
        target = cleaned_data.get("target")
        target = target.id if target else ""

        if self.season != 'FA' and actor != self.initial['actor']:
            raise ValidationError("You may not change the acting unit.")

        try:
            A, T = self.valid[actor][action]
            if assist not in A or target not in T:
                raise ValidationError("Invalid order.")
        except KeyError:
            raise ValidationError("Invalid order.")

        return cleaned_data


class OrderFormSet(BaseFormSet):
    def __init__(self, game, government, first_submit, data=None, **kwargs):
        self.game, self.government = game, government
        self.turn = game.current_turn()
        self.season = self.turn.season
        self.first_submit = first_submit
        super(OrderFormSet, self).__init__(data=data, **kwargs)

    def _construct_forms(self):
        self.forms = [self._construct_form(i, slot=i, valid=v,
                                           season=self.season,
                                           instance=
                                           Order(slot=i, turn=self.turn,
                                                 government=self.government))
                      for i, v in enumerate(validorders(self.game,
                                                        self.government))]

    def save(self):
        for form in self.forms:
            if self.first_submit or form.has_changed():
                form.save()

    def clean(self):
        if any(self.errors):
            return

        if self.total_form_count() > self.initial_form_count():
            raise ValidationError("You may not add orders.")
        if self.total_form_count() < self.initial_form_count():
            raise ValidationError("You may not delete orders.")

        actors = []
        for i in xrange(self.total_form_count()):
            form = self.forms[i]
            actor = form.cleaned_data["actor"].territory
            if not actor:
                continue
            if actor in actors:
                raise ValidationError(
                    "You may not give a territory multiple orders.")
            actors.append(actor)

        if self.season == 'FA':
            builds = self.government.builds_available()
            if builds >= 0 and len(actors) > builds:
                raise ValidationError("You may not build more units than you have supply centers.")
            if builds < 0 and len(actors) != abs(builds):
                u = "unit" if builds == -1 else "units"
                msg = "You must disband exactly %d %s." % (abs(builds), u)
                raise ValidationError(msg)
