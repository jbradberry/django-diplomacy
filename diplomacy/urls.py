from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'diplomacy.views.games_list'),
    (r'^games/$', 'diplomacy.views.games_list'),
    (r'^games/page/(?P<page>\w+)/$', 'diplomacy.views.games_list'),
    (r'^games/status/(?P<state>\w+)/$', 'diplomacy.views.games_list'),
    (r'^games/status/(?P<state>\w+)/page/(?P<page>\w+)/$',
     'diplomacy.views.games_list'),
    (r'^games/name/(?P<slug>[-\w]+)/$',
     'diplomacy.views.games_detail'),
    (r'^games/name/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/$',
     'diplomacy.views.turns_detail'),
    (r'^games/name/(?P<slug>[-\w]+)/map/$',
     'diplomacy.views.map_view'),
    (r'^games/name/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/map/$',
     'diplomacy.views.map_view'),
    (r'^games/name/(?P<slug>[-\w]+)/state/$',
     'diplomacy.views.game_state'),
    (r'^games/name/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/state/$',
     'diplomacy.views.game_state'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$',
     'diplomacy.views.orders'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/filter/$',
     'diplomacy.views.select_filter'),
)
