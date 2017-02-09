import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.views.generic.edit import BaseFormView

from . import models, forms


class GameListView(ListView):
    queryset = models.Game.objects.annotate(
        t=Max('turn__generated')).order_by('-t')


class GameDetailView(DetailView):
    model = models.Game

    def get_context_data(self, **kwargs):
        season, year = self.kwargs.get('season'), self.kwargs.get('year')
        if season is None and year is None:
            t = self.object.current_turn()
            current = t is not None
            setup = not current
        else:
            t = get_object_or_404(
                self.object.turn_set, season=season, year=year)
            current, setup = False, False

        context = {'turn': t, 'current': current, 'setup': setup,
                   'governments': self.object.governments(t)}
        context.update(**kwargs)
        return super(GameDetailView, self).get_context_data(**context)


class GameMasterView(DetailView, BaseFormView):
    model = models.Game
    form_class = forms.GameMasterForm
    template_name = 'diplomacy/game_master.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GameMasterView, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(
            self.get_context_data(object=self.object,
                                  form=form)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(GameMasterView, self).post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super(GameMasterView, self).get_object(queryset)
        if self.request.user != obj.owner:
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = {
            'actors': sum(
                len(g.actors()) for g in self.object.government_set.all())
        }
        context.update(**kwargs)
        return super(GameMasterView, self).get_context_data(**context)

    def form_valid(self, form):
        # FIXME: We should validate the input plus state.
        if self.request.POST.get('activate') and self.object.state == 'S':
            self.object.activate()
        if self.request.POST.get('generate') and self.object.state == 'A':
            self.object.generate()
        if self.request.POST.get('pause') and self.object.state == 'A':
            self.object.state = 'P'
            self.object.save()
        if self.request.POST.get('close') and self.object.state == 'A':
            self.object.state = 'F'
            self.object.save()
        if self.request.POST.get('unpause') and self.object.state == 'P':
            self.object.state = 'A'
            self.object.save()
        return super(GameMasterView, self).form_valid(form)

    def get_success_url(self):
        return reverse('diplomacy_game_master',
                       kwargs={'slug': self.object.slug})


class OrdersView(DetailView, BaseFormView):
    model = models.Government
    slug_field = 'power__name__iexact'

    form_class = formset_factory(form=forms.OrderForm,
                                 formset=forms.OrderFormSet,
                                 extra=0)

    template_name = 'diplomacy/manage_orders.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrdersView, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(
            self.get_context_data(object=self.object,
                                  form=form)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(OrdersView, self).post(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(
            game__slug=self.kwargs.get('gameslug', ''))

    def get_object(self, queryset=None):
        obj = super(OrdersView, self).get_object(queryset)

        if self.request.user != obj.user:
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        order_filter = {
            'unit_fixed': (self.object.game.current_turn().season != 'FA'),
            'tree': self.object.filter_orders()
        }
        context = {
            'game': self.object.game,
            'turn': self.object.game.current_turn(),
            'current': True,
            'order_filter': json.dumps(order_filter),
        }
        context.update(**kwargs)
        return super(OrdersView, self).get_context_data(**context)

    def get_initial(self):
        return [
            {'actor': models.subregion_obj(o['actor']),
             'action': o['action'],
             'assist': models.subregion_obj(o['assist']),
             'target': models.subregion_obj(o['target']),
             'via_convoy': o['via_convoy']}
            for o in self.object.game.current_turn().normalize_orders(self.object)
        ]

    def get_form_kwargs(self):
        kwargs = super(OrdersView, self).get_form_kwargs()
        kwargs.update(
            government=self.object,
        )
        return kwargs

    def form_valid(self, form):
        orders = form.save(commit=False)
        post = models.OrderPost.objects.create(
            government=self.object,
            turn=self.object.game.current_turn()
        )
        for order in orders:
            order.post = post
            order.save()

        messages.success(self.request, "Your orders have been submitted.",
                         fail_silently=True)
        prefs = models.DiplomacyPrefs.objects.filter(user=self.request.user)
        if prefs and prefs.get().warnings:
            for w in form.irrational_orders():
                messages.warning(self.request, w, fail_silently=True)
        return super(OrdersView, self).form_valid(form)

    def get_success_url(self):
        return reverse('diplomacy_orders',
                       kwargs={'gameslug': self.object.game.slug,
                               'slug': self.object.power.name})


class MapView(DetailView):
    model = models.Game
    template_name = 'diplomacy/map.html'

    def get_context_data(self, **kwargs):
        season, year = self.kwargs.get('season'), self.kwargs.get('year')
        if season is None and year is None:
            t = self.object.current_turn()
        else:
            t = get_object_or_404(
                self.object.turn_set, season=season, year=year)

        context = {'turn': t}
        context.update(**kwargs)
        return super(MapView, self).get_context_data(**context)
