from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list, object_detail
from diplomacy.models import Game

game_info = {
    "queryset": Game.objects.all(),
    "template_object_name": "game",
    }

urlpatterns = patterns('',
    # DEVELOPMENT ONLY
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '/home/jrb/dev/apps/diplomacy/media/'}),
    # END DEVELOPMENT ONLY
    (r'^$', object_list, game_info),
    (r'^games/$', object_list, game_info),
    (r'^(?P<state>\w+)/$', 'diplomacy.views.state_lists'),
    (r'^games/(?P<slug>[-\w]+)/$', object_detail, game_info),
    (r'^games/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$', 'diplomacy.views.orders'),
)
