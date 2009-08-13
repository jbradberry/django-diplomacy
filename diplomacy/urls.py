from django.conf.urls.defaults import *
from django.views.generic import list_detail
from diplomacy.models import Game

game_info = {
    "queryset": Game.objects.filter(state__in=('A', 'P')),
    "template_object_name": "game",
    }

urlpatterns = patterns('',
    (r'^$', list_detail.object_list, game_info),
)
