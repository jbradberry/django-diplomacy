from collections import defaultdict

from django.forms import Form, CharField, Textarea, ValidationError
from django.forms.models import ModelForm, BaseFormSet, ModelChoiceField

from .models import Order, Subregion, Unit, territory, borders, find_convoys, subregion_key
from .helpers import unit


msgs = {'s-hold': "{0} has an order to support {1} to hold, but {1} does not"
                  " have an order to hold, support, or convoy.",
        's-move': "{0} has an order to support {1} to move into {2}, but {1}"
                  " does not have an order to move to {2}.",
        'c-move': "{0} has an order to convoy {1} into {2}, but {1} does not"
                  " have an order to move to {2}.",
        'm-conv': "{0} has an order to move to {1}, but this move requires"
                  " a convoy from at least one of your units that has not"
                  " been issued.",
        'm-move': "{0} have been issued orders to move into {1}.  No more than"
                  " one of these orders can succeed.  Perhaps you want to"
                  " support instead?",
        'm-hold': "{0} has been issued an order to move into {1}, but {2}"
                  " has orders to hold (or support or convoy).  You cannot"
                  " dislodge your own units.",
        'm-xing': "{0} and {1} have been issued orders into each other's"
                  " territories.  This will not work unless you convoy one"
                  " of them."}


def join(*args):
    args = [unit(u) for u in args]
    args[-1] = "and {0}".format(args[-1])
    j = ", " if len(args) > 2 else " "
    return j.join(args)


class UnitProxyChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return unit(obj)


class OrderForm(ModelForm):
    qs = Subregion.objects.select_related('territory__name').all()

    actor = UnitProxyChoiceField(queryset=qs, required=False)
    assist = UnitProxyChoiceField(queryset=qs, required=False)
    target = ModelChoiceField(queryset=qs, required=False)

    class Meta:
        model = Order
        exclude = ('post',)

    def __init__(self, *args, **kwargs):
        self.government = kwargs.pop('government', None)

        super(OrderForm, self).__init__(*args, **kwargs)

        my_css = {'actor': 'unit',
                  'action': 'action',
                  'assist': 'unit',
                  'target': 'subregion',}
        for w, c in my_css.iteritems():
            self.fields[w].widget.attrs['class'] = c

    def clean(self):
        turn = self.government.game.current_turn()
        actor = self.cleaned_data.get('actor')
        if turn.season == 'FA':
            # Fall Adjustment builds are optional.
            if self.government.builds_available() > 0 and actor is None:
                return {}
        else:
            if actor != self.initial['actor']:
                raise ValidationError("You may not change the acting unit.")

        order = self.initial.copy()
        order.update(self.cleaned_data)
        if not turn.is_legal(order):
            raise ValidationError("Illegal order.")

        return self.cleaned_data


class OrderFormSet(BaseFormSet):
    def __init__(self, government, data=None, **kwargs):
        self.government = government
        self.turn = government.game.current_turn()
        self.season = self.turn.season

        super(OrderFormSet, self).__init__(data=data, **kwargs)

    def _construct_form(self, *args, **kwargs):
        kwargs['government'] = self.government
        return super(OrderFormSet, self)._construct_form(*args, **kwargs)

    def save(self, commit=True):
        instances = []
        for form in self.forms:
            instances.append(form.save(commit=commit))
        return instances

    def irrational_orders(self):
        warnings = []
        moves = defaultdict(list)
        cross_moves = set()

        orders = {territory(f.instance.actor): f.instance
                  for f in self.forms}
        for f in self.forms:
            w = None
            actor = f.instance.actor
            action = f.instance.action
            assist = f.instance.assist
            target = f.instance.target

            if action == 'S':
                if assist is None or territory(assist) not in orders:
                    continue
                a_action = orders[territory(assist)].action
                a_target = orders[territory(assist)].target
                if target is None and a_action not in ('H', 'S', 'C'):
                    w = msgs['s-hold'].format(unit(actor), unit(assist))
                    warnings.append(w)
                elif target is not None and (a_action != 'M' or
                                             a_target != target):
                    w = msgs['s-move'].format(
                        unit(actor), unit(assist), target)
                    warnings.append(w)
            elif action == 'C':
                if assist is None or territory(assist) not in orders:
                    continue
                a_action = orders[territory(assist)].action
                a_target = orders[territory(assist)].target
                if a_action != 'M' or a_target != target:
                    w = msgs['c-move'].format(
                        unit(actor), unit(assist), target)
                    warnings.append(w)
            elif action == 'M':
                moves[target].append(f.instance.actor)

                if territory(target) in orders:
                    t_actor = orders[territory(target)].actor
                    t_action = orders[territory(target)].action
                    t_target = orders[territory(target)].target
                    if t_action in ('H', 'S', 'C'):
                        w = msgs['m-hold'].format(
                            unit(actor), target, unit(target))
                        warnings.append(w)
                    elif (t_action == 'M' and
                          territory(t_target) == territory(actor)):
                        if territory(actor) in cross_moves:
                            continue
                        w = msgs['m-xing'].format(unit(actor), unit(t_actor))
                        warnings.append(w)
                        cross_moves.add(territory(actor))
                        cross_moves.add(territory(t_actor))
                if (actor.sr_type == 'L'
                    and (subregion_key(target) not in borders(subregion_key(actor))
                         or f.instance.via_convoy)):

                    fleets = Subregion.objects.filter(
                        sr_type='S', unit__turn=self.turn
                    ).exclude(territory__subregion__sr_type='L').distinct()
                    fleets = [subregion_key(sr) for sr in fleets]
                    convoys = find_convoys(self.turn, fleets)

                    fleets = set()
                    for F, A in convoys:
                        if subregion_key(actor) in A and subregion_key(target) in A:
                            fleets = F
                            break
                    for f2 in self.forms:
                        if f2.instance.actor.sr_type != 'S':
                            continue
                        if not (f2.instance.action == 'C' and
                                f2.instance.assist_id == actor.id):
                            fleets.discard(subregion_key(f2.instance.actor))

                    if not any(subregion_key(actor) in A and subregion_key(target) in A
                               for F, A in find_convoys(self.turn, fleets)):
                        w = msgs['m-conv'].format(unit(actor), target)
                        warnings.append(w)

        return warnings + [msgs['m-move'].format(join(*v), t)
                           for t, v in moves.iteritems() if len(v) > 1]

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
            actor = getattr(form.cleaned_data.get('actor'), 'territory', None)
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
                msg = "You must disband exactly {0} {1}.".format(abs(builds), u)
                raise ValidationError(msg)


class GameMasterForm(Form):
    pass
