from django.conf.urls.defaults import *

urlpatterns = patterns('diplomacy.views',
    (r'^$', 'index'),
    (r'^(?P<game_id>\d+)/$', 'detail'),
)
