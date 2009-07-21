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
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
        )
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    year = models.PositiveIntegerField(default=1901)
    season = models.CharField(max_length=2, choices=SEASON_CHOICES, default='S')
    requests = models.ManyToManyField(User, related_name='requests')

class Turn(models.Model):
    game = models.ForeignKey(Game)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

class Power(models.Model):
    name = models.CharField(max_length=20)

class Territory(models.Model):
    name = models.CharField(max_length=30)
    is_supply = models.BooleanField()
    
class Subregion(models.Model):
    SUBREGION_CHOICES = (
        ('L', 'Land'),
        ('S', 'Sea')
        )
    territory = models.ForeignKey(Territory)
    subname = models.CharField(max_length=10, blank=True)
    type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    borders = models.ManyToManyField("self")

class Ambassador(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power, null=True)
    owns = models.ManyToManyField(Territory)

UNIT_CHOICES = (
    ('A', 'Army'),
    ('F', 'Fleet')
    )

class Unit(models.Model):
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
