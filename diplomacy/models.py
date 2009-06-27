from django.db import models
from django.contrib.auth.models import User

SEASON_CHOICES = (
    ('S', 'Spring'),
    ('SR', 'Spring Retreat'),
    ('F', 'Fall'),
    ('FR', 'Fall Retreat'),
    ('FB', 'Fall Build')
    )

class Scenario(models.Model):
    name = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)

class Game(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User)
    scenario = models.ForeignKey(Scenario)
    created = models.DateTimeField(auto_now_add=True)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)

class Ambassador(models.Model):
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=100)
    power = models.CharField(max_length=30, blank=True)

class MTerritory(models.Model):
    name = models.CharField(max_length=30)
    is_supply = models.BooleanField()
    scenario = models.ForeignKey(Scenario)
    owners = models.ManyToManyField(Ambassador)
    
class MSubregion(models.Model):
    SUBREGION_CHOICES = (
        ('L', 'Land'),
        ('S', 'Sea')
        )
    mterritory = models.ForeignKey(MTerritory)
    subname = models.CharField(max_length=10, blank=True)
    type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    borders = models.ManyToManyField("self")

UNIT_CHOICES = (
    ('A', 'Army'),
    ('F', 'Fleet')
    )

class Unit(models.Model):
    owner = models.ForeignKey(Ambassador)
    type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(MSubregion)

class MUnit(models.Model):
    type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(MSubregion)
    

class Order(models.Model):
    ACTION_CHOICES = (
        ('H', 'Hold'),
        ('M', 'Move'),
        ('S', 'Support'),
        ('C', 'Convoy')
        )
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    actor = models.ForeignKey(Unit)
    target = models.ForeignKey(MTerritory, null=True,
                               related_name='targets')
    destination = models.ForeignKey(MTerritory, null=True,
                                    related_name='destinations')
