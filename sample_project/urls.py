from django.conf.urls import include, url
from django.contrib.auth.views import login


urlpatterns = [
    url(r'^', include('diplomacy.urls')),
    url(r'^accounts/login/$', login),
]
