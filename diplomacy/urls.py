from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # DEVELOPMENT ONLY
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '/home/jrb/dev/apps/diplomacy/media/'}),
    # END DEVELOPMENT ONLY
    (r'^$', 'diplomacy.views.games_list'),
    (r'^games/$', 'diplomacy.views.games_list'),
    (r'^games/page/(?P<page>\w+)/$', 'diplomacy.views.games_list'),
    (r'^games/status/(?P<state>\w+)/$', 'diplomacy.views.games_list'),
    (r'^games/status/(?P<state>\w+)/page/(?P<page>\w+)/$',
     'diplomacy.views.games_list'),
    (r'^games/name/(?P<slug>[-\w]+)/$',
     'diplomacy.views.games_detail'),
    (r'^games/name/(?P<slug>[-\w]+)/map/$',
     'diplomacy.views.map_view'),
    (r'^games/name/(?P<slug>[-\w]+)/state/$',
     'diplomacy.views.game_state'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$',
     'diplomacy.views.orders'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/filter/$',
     'diplomacy.views.select_filter'),
)
