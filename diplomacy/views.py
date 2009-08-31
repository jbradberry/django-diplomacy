from django.views.generic.list_detail import object_list
from django.shortcuts import render_to_response
from django.forms.models import modelformset_factory
from django.contrib.auth.decorators import login_required
from diplomacy.models import Game, Order

def state_lists(request, state):
    game_list = Game.objects.filter(state__iexact=state)
    return object_list(request, queryset=game_list,
                       template_object_name="game")

@login_required
def orders(request, slug):
    g = Game.objects.get(slug=slug)
    a = g.ambassador_set.get(user=request.user)
    OrderFormSet = modelformset_factory(Order, exclude=('turn', 'power'))
    if request.method == 'POST':
        formset = OrderFormSet(request.POST,
                               queryset=Order.objects.filter(
                                   power__exact=a.power).filter(
                                   turn__exact=g.current_turn()))
        if formset.is_valid():
            formset.save()
    else:
        formset = OrderFormSet(queryset=Order.objects.filter(
            power__exact=a.power).filter(
            turn__exact=g.current_turn()))
    return render_to_response('diplomacy/manage_orders.html',
                              {'formset': formset})
