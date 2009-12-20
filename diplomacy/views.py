from django.views.generic.list_detail import object_list
from django.shortcuts import render_to_response
from django.forms.models import modelformset_factory, ModelChoiceField
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.utils import simplejson
from django.db.models import ForeignKey
from diplomacy.models import Game, Order, Subregion
from diplomacy.forms import OrderForm, OrderFormSet, validtree

def state_lists(request, state):
    game_list = Game.objects.filter(state__iexact=state)
    return object_list(request, queryset=game_list,
                       template_object_name="game")

@login_required
def orders(request, slug, power):
    g = Game.objects.get(slug=slug)
    try:
        gvt = g.government_set.get(power__name__iexact=power,
                                   user=request.user)
    except ObjectDoesNotExist:
        return HttpResponseForbidden("<h1>Permission denied</h1>")
    qs = Order.objects.filter(government=gvt, turn=g.current_turn())
    sr = Subregion.objects.select_related('territory__name').all()
    def caching_qs(f):
        if isinstance(f, ForeignKey):
            return ModelChoiceField(queryset=sr)
        else:
            return f.formfield()
        
    OFormSet = modelformset_factory(Order, form=OrderForm,
                                    formfield_callback=caching_qs,
                                    formset=OrderFormSet, extra=0,
                                    exclude=('turn', 'government'))
    if request.method == 'POST':
        formset = OFormSet(g, gvt, request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect('../../')
    else:
        formset = OFormSet(g, gvt, queryset=qs)
    return render_to_response('diplomacy/manage_orders.html',
                              {'formset': formset})

def select_filter(request, slug, power):
    g = Game.objects.get(slug=slug)
    uf = (g.current_turn().season != 'FB')
    try:
        gvt = g.government_set.get(power__name__iexact=power)
    except ObjectDoesNotExist:
        raise Http404
    return HttpResponse(simplejson.dumps({'unit_fixed': uf,
                                          'tree': validtree(g, gvt)}),
                        mimetype='application/json')
