from diplomacy.models import Game, Turn, Government, Territory, Subregion
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ('name', 'slug', 'description', 'owner', 'state', 'open_joins')
    list_display = ('name', 'owner', 'created', 'state', 'open_joins')
    prepopulated_fields = {"slug": ("name",)}

class TurnAdmin(admin.ModelAdmin):
    fields = ('game', 'number', 'year', 'season')
    date_hierarchy = 'generated'
    list_display = ('game', 'number', 'year', 'season')

class GovernmentAdmin(admin.ModelAdmin):
    list_display = ('game', 'user', 'name', 'power')

class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'power', 'is_supply')
    ordering = ('power',)

class SubregionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'sr_type', 'init_unit')

admin.site.register(Game, GameAdmin)
admin.site.register(Turn, TurnAdmin)
admin.site.register(Government, GovernmentAdmin)
admin.site.register(Territory, TerritoryAdmin)
admin.site.register(Subregion, SubregionAdmin)
