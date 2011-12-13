from django.views.generic.list_detail import object_list, object_detail
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.simple import direct_to_template
from django.forms.formsets import formset_factory
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.utils import simplejson
from django.db.models import ForeignKey, Max
from diplomacy.models import Game, Government, Turn, Order, Territory, Subregion
from diplomacy.forms import OrderForm, OrderFormSet, GameMasterForm


def game_list(request, page=None, paginate_by=30, state=None, **kwargs):
    game_list = Game.objects.annotate(t=Max('turn__generated')).order_by('-t')

    if state is None:
        state = request.GET.get('state', None)

    if state is not None:
        game_list = game_list.filter(state__iexact=state)
    return object_list(request,
                       queryset=game_list,
                       paginate_by=paginate_by,
                       page=page,
                       template_object_name="game",
                       extra_context={"state": state},
                       **kwargs)

def game_detail(request, slug, season=None, year=None):
    game = get_object_or_404(Game, slug=slug)
    if season is None and year is None:
        t = game.current_turn()
        current = t is not None
        setup = not current
    else:
        t = get_object_or_404(game.turn_set, season=season, year=year)
        current, setup = False, False
    context = {'game': game, 'turn': t, 'current': current,
               'governments': game.governments(t), 'setup': setup}
    return direct_to_template(request, 'diplomacy/game_detail.html',
                              extra_context=context)

@login_required
def game_master(request, slug):
    game = get_object_or_404(Game, slug=slug)
    actors = sum(g.actors().count() for g in game.government_set.all())
    if request.user != game.owner:
        return HttpResponseForbidden("<h1>Permission denied</h1>")
    form = GameMasterForm(request.POST or None)
    if form.is_valid():
        if request.POST.get('activate', False) and game.state == 'S':
            game.activate()
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
        return redirect('diplomacy_game_master', slug=slug)
    return direct_to_template(request, 'diplomacy/game_master.html',
                              extra_context={'game': game, 'form': form,
                                             'actors': actors})

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
                       initial=turn.normalize_orders(gvt))

    if formset.is_valid():
        formset.save()
        return HttpResponseRedirect('../../')

    order_filter = {'unit_fixed': (g.current_turn().season != 'FA'),
                    'tree': gvt.filter_orders()}
    context = {'formset': formset, 'game': g, 'current': True,
               'order_filter': simplejson.dumps(order_filter)}
    return direct_to_template(request, 'diplomacy/manage_orders.html',
                              extra_context=context)

def map_view(request, slug, season=None, year=None):
    game = get_object_or_404(Game, slug=slug)
    if year:
        t = get_object_or_404(Turn, game=g, season=season, year=year)
    else:
        t = game.current_turn()
    context = {'game': game, 'turn': t}
    return direct_to_template(request, 'diplomacy/map.html', context)
