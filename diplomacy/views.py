from django.views.generic.list_detail import object_list
from diplomacy.models import Game

def state_lists(request, state):
    game_list = Game.objects.filter(state__iexact=state)
    return object_list(request, queryset=game_list,
                       template_object_name="game")
