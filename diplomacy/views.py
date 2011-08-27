from django.views.generic.list_detail import object_list, object_detail
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.forms.models import ModelChoiceField
from django.forms.formsets import formset_factory
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.utils import simplejson
from django.db.models import ForeignKey, Max
from diplomacy.models import Game, Government, Turn, Order, Territory, Subregion, Request
from diplomacy.forms import OrderForm, OrderFormSet, JoinRequestForm
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

def games_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    t = game.current_turn()
    return direct_to_template(request, 'diplomacy/game_detail.html',
                              extra_context={'game': game, 'turn': t})

@login_required
def games_join(request, slug):
    game = get_object_or_404(Game, slug=slug)
    context = {'game': game}
    if game.open_joins:
        join = Request.objects.filter(game=game, user=request.user)
        join = join.get() if join else Request(game=game, user=request.user)
        form = JoinRequestForm(request.POST or None,
                               initial={'text': join.text})
        if form.is_valid():
            join.text = form.cleaned_data['text']
            join.active = request.POST.get('join', False)
            join.save()
        context.update(form=form, join=join)
    return direct_to_template(request, 'diplomacy/game_join.html',
                              extra_context=context)

def turns_detail(request, slug, season, year):
    game = get_object_or_404(Game, slug=slug)
    t = get_object_or_404(Turn, game=game, season=season, year=year)
    return direct_to_template(request, 'diplomacy/turn_detail.html',
                              extra_context={'game': game, 'turn': t})

@login_required
def orders(request, slug, power):
    g = Game.objects.get(slug=slug)
    try:
        gvt = g.government_set.get(power__name__iexact=power,
                                   user=request.user)
    except ObjectDoesNotExist:
        return HttpResponseForbidden("<h1>Permission denied</h1>")

    OFormSet = formset_factory(form=OrderForm, formset=OrderFormSet, extra=0)

    turn = g.current_turn()
    order = gvt.order_set.filter(turn=turn)
    formset = OFormSet(gvt, not order.exists(), request.POST or None,
                       initial=turn.canonical_orders(gvt))

    if formset.is_valid():
        formset.save()
        return HttpResponseRedirect('../../')

    return direct_to_template(request, 'diplomacy/manage_orders.html',
                              extra_context={'formset': formset, 'game': g})

# WISHLIST: dump directly to template instead?
def select_filter(request, slug, power):
    g = Game.objects.get(slug=slug)
    uf = (g.current_turn().season != 'FA')
    gvt = get_object_or_404(Government, game=g, power__name__iexact=power)
    return HttpResponse(simplejson.dumps({'unit_fixed': uf,
                                          'tree': gvt.filter_orders()}),
                        mimetype='application/json')

# WISHLIST: dump directly to template instead?
def game_state(request, slug, season=None, year=None):
    colors = {'Austria-Hungary': '#a41a10',
              'England': '#1010a3',
              'France': '#126dc0',
              'Germany': '#5d5d5d',
              'Italy': '#30a310',
              'Russia': '#7110a2',
              'Turkey': '#e6e617'}
    g = Game.objects.get(slug=slug)
    t = g.turn_set.get(
        season=season, year=year) if year else g.current_turn()
    owns = [(re.sub('[ .]', '', T.name.lower()), colors[G.power.name])
            for G in g.government_set.all()
            for T in Territory.objects.filter(ownership__turn=t,
                                              ownership__government=G)]
    return HttpResponse(simplejson.dumps(owns),
                        mimetype='application/json')

def map_view(request, slug, season=None, year=None):
    game = get_object_or_404(Game, slug=slug)
    if year:
        t = get_object_or_404(Turn, game=g, season=season, year=int(year))
    else:
        t = game.current_turn()
    return direct_to_template(request, 'diplomacy/map.html',
                              {'game': game, 'turn': t})
