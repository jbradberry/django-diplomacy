from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import datetime

SEASON_CHOICES = (
    ('S', 'Spring'),
    ('SR', 'Spring Retreat'),
    ('F', 'Fall'),
    ('FR', 'Fall Retreat'),
    ('FA', 'Fall Adjustment')
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
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    requests = models.ManyToManyField(User, related_name='requests')
    accepts = models.ManyToManyField(User, related_name='accepts')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy.views.games_detail', (), {
            'slug': self.slug})

    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()
        else:
            return None

    def generate(self, init=False):
        prev = self.current_turn()

        if init:
            turn = prev
        else:
            turn = self.turn_set.create(number=prev.number+1)

            # proxy code in place of actually moving the units
            for u in Unit.objects.filter(turn=prev):
                Unit.objects.create(turn=turn, government=u.government,
                                    u_type=u.u_type, subregion=u.subregion)

        # do after units are moved
        for t in Territory.objects.all():
            u = Unit.objects.filter(turn=turn, subregion__territory=t)
            assert u.count() < 2
            try:
                if turn.season == 'F' and u.exists():
                    gvt = u[0].government
                else:
                    gvt = self.government_set.get(
                        ownership__turn=prev, ownership__territory=t)
            except ObjectDoesNotExist:
                continue
            Ownership(turn=turn, government=gvt, territory=t).save()

    generate.alters_data = True

def game_changed(sender, **kwargs):
    instance = kwargs['instance']
    if instance.state == 'A' and not instance.turn_set.exists():
        turn = instance.turn_set.create(number=0)
        convert = {'L': 'A', 'S': 'F'}
        for pwr in Power.objects.all():
            gvt = instance.government_set.create(name=pwr.name, power=pwr)
            sr_set = Subregion.objects.filter(territory__power=pwr,
                                              init_unit=True)
            for sr in sr_set:
                gvt.unit_set.create(turn=turn,
                                    u_type=convert[sr.sr_type],
                                    subregion=sr)
        instance.generate(init=True)
post_save.connect(game_changed, sender=Game)

class Turn(models.Model):
    class Meta:
        get_latest_by = 'generated'
        ordering = ['-generated']

    game = models.ForeignKey(Game)
    number = models.IntegerField()
    year = models.IntegerField()
    season = models.CharField(max_length=2, choices=SEASON_CHOICES)
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.get_season_display(), self.year)

    @models.permalink
    def get_absolute_url(self):
        return ('diplomacy.views.turns_detail', (), {
            'game': self.game.slug,
            'turn': '%s%s' % (self.season, self.year)})

    def governments(self):
        gvts = Government.objects.filter(game=self.game)
        owns = Ownership.objects.filter(turn=self, territory__is_supply=True)
        return sorted([(g, sum(1 for t in owns if t.government.id == g.id))
                       for g in gvts], key=lambda x: (-x[1], x[0].power.name))

def turn_create(sender, **kwargs):
    instance = kwargs['instance']
    if instance.id: return
    instance.year = 1900 + instance.number // len(SEASON_CHOICES)
    instance.season = SEASON_CHOICES[instance.number % len(SEASON_CHOICES)][0]
pre_save.connect(turn_create, sender=Turn)

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
            return u'%s (%s)' % (self.territory.name, self.subname)
        else:
            return self.territory.name

class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power)
    owns = models.ManyToManyField(Territory, through='Ownership')

    def __unicode__(self):
        return self.name

    def supplycenters(self, turn=None):
        if not turn:
            turn = self.game.current_turn()
        return self.owns.filter(ownership__turn=turn,
                                is_supply=True).count()

    def units(self, turn=None):
        if not turn:
            turn = self.game.current_turn()
        return Unit.objects.filter(turn=turn, government=self).count()

    def builds_available(self):
        return self.supplycenters() - self.units()

class Ownership(models.Model):
    class Meta:
        unique_together = ("turn", "territory")

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    territory = models.ForeignKey(Territory)

class Unit(models.Model):
    class Meta:
        unique_together = ("turn", "subregion")

    turn = models.ForeignKey(Turn)
    government = models.ForeignKey(Government)
    u_type = models.CharField(max_length=1, choices=UNIT_CHOICES)
    subregion = models.ForeignKey(Subregion)
    displaced_from = models.ForeignKey(Territory, null=True, blank=True,
                                       related_name='displaced')
    standoff_from = models.ForeignKey(Territory, null=True, blank=True,
                                      related_name='standoff')

    def __unicode__(self):
        return u'%s %s' % (self.u_type, self.subregion.territory)

class Order(models.Model):
    class Meta:
        get_latest_by = "timestamp"

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
    timestamp = models.DateTimeField(auto_now_add=True)
    slot = models.PositiveSmallIntegerField()
    actor = models.ForeignKey(Subregion, null=True, blank=True,
                              related_name='actors')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    assist = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='assists')
    target = models.ForeignKey(Subregion, null=True, blank=True,
                               related_name='targets')
