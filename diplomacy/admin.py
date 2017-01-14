from django.contrib import admin

from . import models


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


class DiplomacyPrefsAdmin(admin.ModelAdmin):
    list_display = ('user', 'warnings')


admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Turn, TurnAdmin)
admin.site.register(models.Government, GovernmentAdmin)
admin.site.register(models.Territory, TerritoryAdmin)
admin.site.register(models.Subregion, SubregionAdmin)
admin.site.register(models.DiplomacyPrefs, DiplomacyPrefsAdmin)
