=========
Diplomacy
=========

Diplomacy is a turn-based strategy game, set in Europe at the start of
World War I.  Each player represents one of the seven European Great
Powers.

For game instructions and other useful info, see
`http://www.wizards.com/default.asp?x=ah/prod/diplomacy`

See also `http://en.wikipedia.org/wiki/Diplomacy_(game)`


Requirements
------------

- Python 2.7, 3.5+
- Django >= 1.7, < 2


Recommended
-----------

- `django-turn-generation <https://github.com/jbradberry/django-turn-generation>`_
- `django-postoffice <https://github.com/jbradberry/django-postoffice>`_


Installation
------------

Use pip to install django-diplomacy from github
::

    pip install git+https://github.com/jbradberry/django-diplomacy.git


Configuration
-------------

Add Django Diplomacy to the ``INSTALLED_APPS`` in your settings file.
::

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # Added.
        'diplomacy',
    )

Also, be sure to include ``diplomacy.urls`` in your root urlconf.

Example::

    from django.conf.urls import include, url
    from django.contrib import admin
    from django.contrib.auth.views import login


    urlpatterns = [
        url(r'^', include('diplomacy.urls')),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^accounts/login/$', login),
    ]
