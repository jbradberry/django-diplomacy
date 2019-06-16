from django.conf.urls import include, url


urlpatterns = [
    url(r'^', include('diplomacy.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
