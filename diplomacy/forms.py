from django.forms.models import ModelForm, BaseFormSet, ModelChoiceField
from django.forms import ValidationError
from diplomacy.models import Order, Subregion, Unit

convert = {'L': 'A', 'S': 'F'}

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

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)

        my_css = {'actor': 'subregion',
                  'action': 'action',
                  'assist': 'subregion',
                  'target': 'subregion',}
        for w, c in my_css.iteritems():
            self.fields[w].widget.attrs['class'] = c

    def clean(self):
        turn = self.initial['government'].game.current_turn()
        actor = self.cleaned_data.get("actor")
        if turn.season != 'FA' and actor != self.initial['actor']:
            raise ValidationError("You may not change the acting unit.")

        order = self.initial.copy()
        order.update(self.cleaned_data)
        if not turn.is_legal(order):
            raise ValidationError("Illegal order.")

        return self.cleaned_data


class OrderFormSet(BaseFormSet):
    def __init__(self, government, first_submit, data=None, **kwargs):
        self.government = government
        self.turn = government.game.current_turn()
        self.season = self.turn.season
        self.first_submit = first_submit

        super(OrderFormSet, self).__init__(data=data, **kwargs)

    def _construct_forms(self):
        self.forms = [self._construct_form(i, instance=
                                           Order(slot=x['slot'],
                                                 turn=x['turn'],
                                                 government=x['government']))
                      for i, x in enumerate(self.initial)]

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

        actors = set()
        for i in xrange(self.total_form_count()):
            form = self.forms[i]
            actor = form.cleaned_data["actor"].territory
            if not actor:
                continue
            if actor in actors:
                raise ValidationError(
                    "You may not give a territory multiple orders.")
            actors.add(actor)

        if self.season == 'FA':
            builds = self.government.builds_available()
            if builds >= 0 and len(actors) > builds:
                raise ValidationError("You may not build more units than"
                                      " you have supply centers.")
            if builds < 0 and len(actors) != abs(builds):
                u = "unit" if builds == -1 else "units"
                msg = "You must disband exactly %d %s." % (abs(builds), u)
                raise ValidationError(msg)
