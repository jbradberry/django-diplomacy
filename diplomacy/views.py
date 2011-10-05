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
from diplomacy.forms import OrderForm, OrderFormSet, JoinRequestForm, GameMasterForm
import re


colors = {'Austria-Hungary': '#a41a10',
          'England': '#1010a3',
          'France': '#126dc0',
          'Germany': '#5d5d5d',
          'Italy': '#30a310',
          'Russia': '#7110a2',
          'Turkey': '#e6e617'}
colors = simplejson.dumps(colors)

def map_state(game, turn):
    owns = [(re.sub('[ .]', '', T.name.lower()), G.power.name)
            for G in game.government_set.all()
            for T in Territory.objects.filter(ownership__turn=turn,
                                              ownership__government=G)]
    return {'state': simplejson.dumps(owns), 'colors': colors}

def game_list(request, page=1, paginate_by=30, state=None):
    game_list = Game.objects.annotate(t=Max('turn__generated')).order_by('-t')
    if state:
        game_list = game_list.filter(state__iexact=state)
    return object_list(request,
                       queryset=game_list,
                       paginate_by=paginate_by,
                       page=page,
                       template_object_name="game",
                       extra_context={"state": state})

def game_detail(request, slug, season=None, year=None):
    game = get_object_or_404(Game, slug=slug)
    if season is None and year is None:
        t, current = game.current_turn(), True
    else:
        t = get_object_or_404(game.turn_set, season=season, year=year)
        current = False
    context = {'game': game, 'turn': t, 'current_turn': current,
               'width': 477, 'height': 400}
    context.update(**map_state(game, t))
    return direct_to_template(request, 'diplomacy/game_detail.html',
                              extra_context=context)

@login_required
def game_join(request, slug):
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

@login_required
def game_master(request, slug):
    game = get_object_or_404(Game, slug=slug)
    if request.user != game.owner:
        return HttpResponseForbidden("<h1>Permission denied</h1>")
    form = GameMasterForm(request.POST or None)
    if form.is_valid():
        if request.POST.get('activate', False) and game.state == 'S':
            game.state = 'A'
            game.save()
        if request.POST.get('generate', False) and game.state == 'A':
            game.generate()
        if request.POST.get('pause', False) and game.state == 'A':
            game.state = 'P'
            game.save()
        if request.POST.get('close', False) and game.state == 'A':
            game.state = 'F'
            game.save()
        if request.POST.get('unpause', False) and game.state == 'P':
            game.state = 'A'
            game.save()
    return direct_to_template(request, 'diplomacy/game_master.html',
                              extra_context={'game': game, 'form': form})

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

    context = {'formset': formset, 'game': g, 'width': 477, 'height': 400}
    context.update(**map_state(g, turn))
    return direct_to_template(request, 'diplomacy/manage_orders.html',
                              extra_context=context)

# WISHLIST: dump directly to template instead?
def select_filter(request, slug, power):
    g = Game.objects.get(slug=slug)
    uf = (g.current_turn().season != 'FA')
    gvt = get_object_or_404(Government, game=g, power__name__iexact=power)
    return HttpResponse(simplejson.dumps({'unit_fixed': uf,
                                          'tree': gvt.filter_orders()}),
                        mimetype='application/json')

def map_view(request, slug, season=None, year=None):
    game = get_object_or_404(Game, slug=slug)
    if year:
        t = get_object_or_404(Turn, game=g, season=season, year=year)
    else:
        t = game.current_turn()
    context = {'game': game, 'turn': t, 'width': 715, 'height': 600}
    context.update(**map_state(game, t))
    return direct_to_template(request, 'diplomacy/map.html', context)
