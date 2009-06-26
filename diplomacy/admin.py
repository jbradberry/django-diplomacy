from diplomacy.models import Game
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ['name', 'owner']

admin.site.register(Game, GameAdmin)
