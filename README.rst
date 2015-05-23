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
- Python >= 2.6
- Django >= 1.3, < 1.7

Recommended
-----------
- django-micro-press

Installation
------------

Use pip to install Django Diplomacy from github

    pip install git+https://github.com/jbradberry/django-diplomacy.git


Configuration
-------------

Add Django Diplomacy to the `INSTALLED_APPS` in your settings file.

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

Also, be sure to include `diplomacy.urls` in your root urlconf.

Example:

    urlpatterns = patterns('',
        (r'^', include('diplomacy.urls')),
        (r'^admin/', include(admin.site.urls)),
    )
