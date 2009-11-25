from django.forms.models import ModelForm, BaseModelFormSet
from django.forms.fields import ChoiceField
from django.db.models import Q
from diplomacy.models import Order, Subregion, Unit

class OrderForm(ModelForm):
    actor = ChoiceField()
    target = ChoiceField()
    destination = ChoiceField()
    
    class Meta:
        model = Order
        exclude = ('turn', 'government')
        
    def __init__(self, game, government, names, sr, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.game = game
        self.government = government
        self.names = names
        self.season = game.current_turn().season

        my_css = {'u_type': 'u_type',
                  'actor': 'subregion',
                  'action': 'action',
                  'target': 'subregion',
                  'destination': 'subregion'}
        for w, c in my_css.items():
            self.fields[w].widget.attrs['class'] = c

        self.fields['actor'].choices = self.names.items()
        u = Subregion.objects.get(id=self.initial['actor'])
        if self.season in ('S', 'F'):
            if self.initial['u_type'] == 'F':
                self._constrain('action', ('H', 'M', 'S', 'C'))
                self._filter('target', ('H',),
                             H=sr.none(),
                             M=sr.filter(borders=u),
                             S=sr.filter(unit__government__game=self.game),
                             C=sr.filter(unit__government__game=self.game,
                                         unit__u_type='A',
                                         territory__subregion__sr_type='S'))
                self._filter('destination', ('H', 'M', 'S'),
                             H=sr.none(),
                             M=sr.none(),
                             S=sr.filter(borders=u),
                             C=sr.filter(sr_type='L').filter(
                                 territory__subregion__sr_type='S'
                                 ).distinct())
            if self.initial['u_type'] == 'A':
                self._constrain('action', ('H', 'M', 'S'))
                self._filter('target', ('H',),
                             H=sr.none(),
                             M=sr.filter(sr_type='L').filter(
                                 Q(borders=u) |
                                 Q(territory__subregion__sr_type='S')
                                 ).distinct(),
                             S=sr.filter(unit__government__game=self.game))
                self._filter('destination', ('H', 'M', 'S'),
                             H=sr.none(),
                             M=sr.none(),
                             S=sr.filter(borders=u))
        if self.season in ('SR', 'FR'):
            self._constrain('action', ('M', 'D'))
            self._remove('destination')
            self._filter('target', ('D',), M=sr.filter(borders=u),
                         D=sr.none())
        if self.season == 'FB':
            self._remove('target', 'destination')
            if government.builds_available() < 0: # need to disband
                self._one('action', 'D')
                qs = sr.filter(unit__government=me)
                self._filter('actor', (), F=qs.filter(sr_type='S'),
                             A=qs.filter(sr_type='L'))
            if government.builds_available() > 0: # allowed to build
                self._one('action', 'B')
                qs = sr.filter(territory__government=me,
                               territory__power__government=me,
                               territory__is_supply=True).exclude(
                    territory__subregion__unit__government__game=self.game)
                self._filter('actor', (), F=qs.filter(sr_type='S'),
                             A=qs.filter(sr_type='L'))
            if government.builds_available() == 0:
                raise ValueError("No orders are permitted.")
        else: # unless it is a build phase, there is a fixed set of orders.
            self._one('u_type')
            self._one('actor')

    def _filter(self, fn, allow_null, **kwargs):
        if allow_null:
            self.fields[fn].required = False
        empty_label = u"---------"
        choices = [(k, (((u'', empty_label),) if k in allow_null else ()) +
                    tuple((i.pk, self.names[i.pk]) for i in v))
                   for k, v in kwargs.items()]
        self.fields[fn].choices = choices

    def _constrain(self, fn, lst):
        self.fields[fn].choices = [i for i in self.fields[fn].choices
                                   if i[0] in lst]

    def _one(self, fn, choice=None):
        if choice is None:
            choice = self.initial[fn]
        old = self.fields[fn].choices
        self.fields[fn].choices = [c for c in old if c[0] == choice]

    def _remove(self, *args):
        for fn in args:
            del self.fields[fn]

    def clean(self):
        for i in ('actor', 'target', 'destination'):
            value = self.cleaned_data[i]
            if value:
                self.cleaned_data[i] = Subregion.objects.get(pk=value)
            else:
                self.cleaned_data[i] = None
        return self.cleaned_data

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
