from django.conf.urls.defaults import patterns, url, include
from django.conf import settings

from . import views


urlpatterns = patterns('',
    url(r'^games/$', views.GameListView.as_view(), name='diplomacy_game_list'),
    url(r'^games/(?P<slug>[-\w]+)/$', views.GameDetailView.as_view(),
        name='diplomacy_game_detail'),
    url(r'^games/(?P<slug>[-\w]+)/master/$', views.GameMasterView.as_view(),
        name='diplomacy_game_master'),
    url(r'^games/(?P<slug>[-\w]+)/map/$', views.MapView.as_view(),
        name='diplomacy_game_map'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/$',
        views.GameDetailView.as_view(), name='diplomacy_turn_detail'),
    url(r'^games/(?P<slug>[-\w]+)/turn/(?P<season>[A-Z]+)(?P<year>\d+)/map/$',
        views.MapView.as_view(), name='diplomacy_turn_map'),
    url(r'^games/(?P<gameslug>[-\w]+)/orders/(?P<slug>[-\w]+)/$',
        views.OrdersView.as_view(), name='diplomacy_orders'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="diplomacy", app_name="micropress"),
         {'realm_content_type': 'diplomacy.Game'}),
    )
