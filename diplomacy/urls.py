from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('diplomacy.views',
    #(r'^$', 'game_list'),
    url(r'^games/$', 'game_list', name='game_list'),
    url(r'^games/(?P<slug>[-\w]+)/$', 'game_detail', name='game_detail'),
    (r'^games/(?P<slug>[-\w]+)/master/$', 'game_master'),
    url(r'^games/(?P<slug>[-\w]+)/map/$', 'map_view', name='game_map'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/$',
        'game_detail', name='turn_detail'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/map/$',
        'map_view', name='turn_map'),
    (r'^games/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/$', 'orders'),
    (r'^games/(?P<slug>[-\w]+)/orders/(?P<power>[-\w]+)/filter/$',
     'select_filter'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', app_name="diplomacy"),
         {'realm_content_type': 'diplomacy.Game'}),
    )
