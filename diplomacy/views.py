from django.views.generic.list_detail import object_list, object_detail
from django.shortcuts import render_to_response, get_object_or_404
from django.forms.models import modelformset_factory, ModelChoiceField
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.utils import simplejson
from django.db.models import ForeignKey, Max
from diplomacy.models import Game, Order, Subregion
from diplomacy.forms import OrderForm, OrderFormSet, validorders
import re

def games_list(request, page=1, paginate_by=30, state=None):
    game_list = Game.objects.annotate(t=Max('turn__generated')).order_by('-t')
    if state:
        game_list = game_list.filter(state__iexact=state)
    return object_list(request,
                       queryset=game_list,
                       paginate_by=paginate_by,
                       page=page,
                       template_object_name="game",
                       extra_context={"state": state})

def games_detail(request, slug, turn=None): # FIXME
    game_list = Game.objects.all()
    return object_detail(request,
                         queryset=game_list,
                         slug=slug,
                         template_object_name="game",
                         extra_context={"turn": turn})

@login_required
def orders(request, slug, power):
    g = Game.objects.get(slug=slug)
    try:
        gvt = g.government_set.get(power__name__iexact=power,
                                   user=request.user)
    except ObjectDoesNotExist:
        return HttpResponseForbidden("<h1>Permission denied</h1>")

    OFormSet = modelformset_factory(Order, form=OrderForm,
                                    formset=OrderFormSet, extra=0,
                                    exclude=('turn', 'government', 'timestamp'))

    formset = OFormSet(g, gvt, request.POST or None)
    if formset.is_valid():
        formset.save()
        return HttpResponseRedirect('../../')

    return render_to_response('diplomacy/manage_orders.html',
                              {'formset': formset})

def select_filter(request, slug, power):
    g = Game.objects.get(slug=slug)
    uf = (g.current_turn().season != 'FA')
    gvt = get_object_or_404(Government, game=g, power__name__iexact=power)
    return HttpResponse(simplejson.dumps({'unit_fixed': uf,
                                          'tree': validorders(g, gvt)}),
                        mimetype='application/json')

def game_state(request, slug, turn=None): # FIXME
    colors = {'Austria-Hungary': '#a41a10',
              'England': '#1010a3',
              'France': '#126dc0',
              'Germany': '#5d5d5d',
              'Italy': '#30a310',
              'Russia': '#7110a2',
              'Turkey': '#e6e617'}
    g = Game.objects.get(slug=slug)
    owns = [(re.sub('[ .]', '', T.name.lower()), colors[G.power.name])
            for G in g.government_set.all()
            for T in G.owns.all()]
    return HttpResponse(simplejson.dumps(owns),
                        mimetype='application/json')

def map_view(request, slug, turn=None): # FIXME
    game = Game.objects.get(slug=slug)
    return render_to_response('diplomacy/map.html', {'game': game})
