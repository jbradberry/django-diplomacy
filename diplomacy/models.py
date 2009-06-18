from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(models.User)

class Ambassador(models.Model):
    user = models.ForeignKey(models.User)
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=50)
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

class Border(models.Model):
    region1 = models.ForeignKey(Subregion)
    region2 = models.ForeignKey(Subregion)

class Unit(models.Model):
    UNIT_CHOICES = (
        ('A', 'Army'),
        ('F', 'Fleet')
        )
    owner = models.ForeignKey(Ambassador)
    type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)

class Order(models.Model):
    SEASON_CHOICES = (
        ('S', 'Spring'),
        ('SR', 'Spring Retreat'),
        ('F', 'Fall'),
        ('FR', 'Fall Retreat'),
        ('FB', 'Fall Build')
        )
    ACTION_CHOICES = (
        ('H', 'Hold')
        ('M', 'Move')
        ('S', 'Support')
        ('C', 'Convoy')
        )
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    actor = models.ForeignKey(Unit)
    target = models.ForeignKey(Territory, null=True)
    destination = models.ForeignKey(Territory, null=True)
