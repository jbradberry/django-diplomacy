from django.db import models
from django.contrib.auth.models import User
import datetime

def get_next(current, choiceset):
    choices = (i[0] for i in choiceset+choiceset[0])
    for i in choices:
        if i == current:
            return choices.next()

SEASON_CHOICES = (
    ('S', 'Spring'),
    ('SR', 'Spring Retreat'),
    ('F', 'Fall'),
    ('FR', 'Fall Retreat'),
    ('FB', 'Fall Build')
    )

UNIT_CHOICES = (
    ('A', 'Army'),
    ('F', 'Fleet')
    )

SUBREGION_CHOICES = (
    ('L', 'Land'),
    ('S', 'Sea')
    )

class Game(models.Model):
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
        )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    requests = models.ManyToManyField(User, related_name='requests')
    accepts = models.ManyToManyField(User, related_name='accepts')

    def __unicode__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)
        self.old_state = self.state

    def save(self, force_insert=False, force_update=False):
        if self.old_state == 'S' and self.state == 'A':
            self.started = datetime.datetime.now()
            self.turn_set.create(year=1901, season='S')
        super(Game, self).save(force_insert, force_update)
        self.old_state = self.state

    def get_absolute_url(self):
        return "/diplomacy/games/%s/" % self.slug

class Turn(models.Model):
    game = models.ForeignKey(Game)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated']

    def __unicode__(self):
        return "%s %s" % (self.get_season_display(), self.year)

    def generate(self):
        Y = self.year if self.season != 'FB' else self.year + 1 # Python 2.5
        S = get_next(self.season, SEASON_CHOICES)
        new = Turn(game=self.game, year=Y, season=S)
        new.save()

class Power(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name

class Territory(models.Model):
    name = models.CharField(max_length=30)
    power = models.ForeignKey(Power, null=True, blank=True)
    is_supply = models.BooleanField()

    def __unicode__(self):
        return self.name
    
class Subregion(models.Model):
    territory = models.ForeignKey(Territory)
    subname = models.CharField(max_length=10, blank=True)
    sr_type = models.CharField(max_length=1, choices=SUBREGION_CHOICES)
    init_unit = models.BooleanField()
    borders = models.ManyToManyField("self", null=True, blank=True)

    def __unicode__(self):
        if self.subname:
            return u'%s (%s)' % (self.territory, self.subname)
        else:
            return u'%s [%s]' % (self.territory, self.sr_type)

class Ambassador(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power, null=True, blank=True)
    owns = models.ManyToManyField(Territory)

    def __unicode__(self):
        return self.name

class Unit(models.Model):
    owner = models.ForeignKey(Ambassador)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)

    def __unicode__(self):
        return self.subregion

class Order(models.Model):
    ACTION_CHOICES = (
        ('H', 'Hold'),
        ('M', 'Move'),
        ('S', 'Support'),
        ('C', 'Convoy'),
        ('B', 'Build'),
        ('D', 'Disband')
        )
    turn = models.ForeignKey(Turn)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    actor = models.ForeignKey(Territory, null=True, blank=True,
                              related_name='actors')
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES, blank=True) 
    target = models.ForeignKey(Territory, null=True, blank=True,
                               related_name='targets')
    destination = models.ForeignKey(Territory, null=True, blank=True,
                                    related_name='destinations')
