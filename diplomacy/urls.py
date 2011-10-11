from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('diplomacy.views',
    #(r'^$', 'game_list'),
    url(r'^games/$', 'game_list', name='game_list'),
    (r'^games/page/(?P<page>\w+)/$', 'game_list'),
    (r'^games/status/(?P<state>\w+)/$', 'game_list'),
    (r'^games/status/(?P<state>\w+)/page/(?P<page>\w+)/$', 'game_list'),
    url(r'^games/name/(?P<slug>[-\w]+)/$', 'game_detail', name='game_detail'),
    (r'^games/name/(?P<slug>[-\w]+)/join/$', 'game_join'),
    (r'^games/name/(?P<slug>[-\w]+)/master/$', 'game_master'),
    url(r'^games/name/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/$',
     'game_detail', name='turn_detail'),
    (r'^games/name/(?P<slug>[-\w]+)/map/$', 'map_view'),
    (r'^games/name/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/map/$',
     'map_view'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$', 'orders'),
    (r'^games/name/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/filter/$',
     'select_filter'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/name/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="diplomacy",
                 app_name="micropress"),
         {'realm_content_type': 'diplomacy.Game'}),
    )
