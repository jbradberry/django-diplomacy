from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('diplomacy.views',
    url(r'^games/$', 'game_list', name='diplomacy_game_list'),
    url(r'^games/(?P<slug>[-\w]+)/$', 'game_detail', name='diplomacy_game_detail'),
    url(r'^games/(?P<slug>[-\w]+)/master/$', 'game_master', name='diplomacy_game_master'),
    url(r'^games/(?P<slug>[-\w]+)/map/$', 'map_view', name='diplomacy_game_map'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/$',
        'game_detail', name='diplomacy_turn_detail'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/map/$',
        'map_view', name='diplomacy_turn_map'),
    url(r'^games/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$', 'orders', name='diplomacy_orders'),
    url(r'^games/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/filter/$',
     'select_filter', name='diplomacy_select_filter'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="diplomacy", app_name="micropress"),
         {'realm_content_type': 'diplomacy.Game'}),
    )
