from django.views.generic.list_detail import object_list
from django.shortcuts import render_to_response
from django.forms.models import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from diplomacy.models import Game, Order
from diplomacy.forms import OrderForm, OrderFormSet

def state_lists(request, state):
    game_list = Game.objects.filter(state__iexact=state)
    return object_list(request, queryset=game_list,
                       template_object_name="game")

@login_required
def orders(request, slug):
    g = Game.objects.get(slug=slug)
    gvt = g.government_set.get(user=request.user)
    qs = Order.objects.filter(government=gvt, turn=g.current_turn())
    OFormSet = modelformset_factory(Order, form=OrderForm,
                                    formset=OrderFormSet, extra=0,
                                    exclude=('turn', 'government'))
    if request.method == 'POST':
        formset = OFormSet(request.POST, g, gvt, queryset=qs)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect('../')
    else:
        formset = OFormSet(g, gvt, queryset=qs)
    return render_to_response('diplomacy/manage_orders.html',
                              {'formset': formset})
