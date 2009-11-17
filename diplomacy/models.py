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
            convert = {'L': 'A', 'S': 'F'}
            self.started = datetime.datetime.now()
            for pwr in Power.objects.all():
                t_set = Territory.objects.filter(power=pwr)
                gvt = self.government_set.create(name=pwr.name, power=pwr,
                                                 owns=t_set)
                for sr in Subregion.objects.filter(init_unit=True,
                                                   territory__power=pwr):
                    gvt.unit_set.create(u_type=convert[sr.sr_type],
                                        subregion=sr)
            self.generate(start=True)
        super(Game, self).save(force_insert, force_update)
        self.old_state = self.state
    save.alters_data = True

    def get_absolute_url(self):
        return "/diplomacy/games/%s/" % self.slug

    def current_turn(self):
        if self.turn_set.count() > 0:
            return self.turn_set.order_by('-generated')[0]
        else:
            return "Setup"

    def generate(self, start=False):
        if start:
            Y, S = 1901, 'S'
        else:
            turn = self.current_turn()
            Y = turn.year if turn.season != 'FB' else turn.year + 1
            S = get_next(turn.season, SEASON_CHOICES)
        turn = self.turn_set.create(year=Y, season=S) # FIXME
        for u in Unit.objects.filter(government__game=self):
            turn.order_set.create(government=u.government,
                                  u_type=u.u_type,
                                  actor=u.subregion,
                                  action='H')
    generate.alters_data = True

class Turn(models.Model):
    game = models.ForeignKey(Game)
    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.get_season_display(), self.year)

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

class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power)
    owns = models.ManyToManyField(Territory)

    def __unicode__(self):
        return self.name

    def supplycenters(self):
        return self.owns.filter(is_supply=True).count()

    def units(self):
        return Unit.objects.filter(government=self).count()

    def builds_available(self):
        return self.supplycenters() - self.units()

class Unit(models.Model):
    government = models.ForeignKey(Government)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)

    def __unicode__(self):
        return u'%s %s' % (self.u_type, self.subregion.territory)

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
    government = models.ForeignKey(Government)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES, blank=True) 
    actor = models.ForeignKey(Subregion, null=True, blank=True,
                              related_name='actors')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='targets')
    destination = models.ForeignKey(Subregion, null=True, blank=True,
                                    related_name='destinations')
