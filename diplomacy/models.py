from django.db import models
from django.contrib.auth.models import User

SEASON_CHOICES = (
    ('S', 'Spring'),
    ('SR', 'Spring Retreat'),
    ('F', 'Fall'),
    ('FR', 'Fall Retreat'),
    ('FB', 'Fall Build')
    )

class Game(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)

class Ambassador(models.Model):
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=30, blank=True)

class Territory(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=30)
    is_supply = models.BooleanField()
    owner = models.ForeignKey(Ambassador, null=True)

class Subregion(models.Model):
    SUBREGION_CHOICES = (
        ('L', 'Land'),
        ('S', 'Sea')
        )
    territory = models.ForeignKey(Territory)
    subname = models.CharField(max_length=10, blank=True)
    type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    borders = models.ManyToManyField("self")

class Unit(models.Model):
    UNIT_CHOICES = (
        ('A', 'Army'),
        ('F', 'Fleet')
        )
    owner = models.ForeignKey(Ambassador)
    type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)

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
    target = models.ForeignKey(Territory, null=True,
                               related_name='targets')
    destination = models.ForeignKey(Territory, null=True,
                                    related_name='destinations')
