from diplomacy.models import Game, Territory, Subregion
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ['name', 'slug', 'owner', 'state']
    list_display = ('name', 'owner', 'created', 'state')
    prepopulated_fields = {"slug": ("name",)}

class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'power', 'is_supply')
    ordering = ('power',)

class SubregionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'sr_type', 'init_unit')

admin.site.register(Game, GameAdmin)
admin.site.register(Territory, TerritoryAdmin)
admin.site.register(Subregion, SubregionAdmin)
