from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list, object_detail
from diplomacy.models import Game

game_info = {
    "queryset": Game.objects.all(), #.filter(state__in=('A', 'P')),
    "template_object_name": "game",
    }

urlpatterns = patterns('',
    (r'^$', object_list, game_info),
    (r'^games/$', object_list, game_info),
    (r'^(?P<state>\w+)/$', 'diplomacy.views.state_lists'),
    (r'^games/(?P<slug>[-\w]+)/$', object_detail, game_info),
)
