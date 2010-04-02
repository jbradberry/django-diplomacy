from django.db import models
from django.db.models import aggregates, sql
from django.db.models.signals import post_save
from django.contrib.auth.models import User
import datetime

class CountNullIf(sql.aggregates.Count):
    sql_template = '%(function)s(NULLIF(%(field)s,FALSE))'
sql.aggregates.CountNullIf = CountNullIf

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
        return self.turn_set.latest()

    def governments(self):
        sup = aggregates.Count('owns__is_supply')
        sup.name = 'CountNullIf'
        return self.government_set.all().annotate(sc=sup).order_by(
            '-sc', 'power__name')

    def generate(self, start=False):
        if start:
            self.turn_set.create(year=1900, season='FA')
            return
        else:
            turn = self.current_turn()
            Y = turn.year if turn.season != 'FA' else turn.year + 1
            S = get_next(turn.season, SEASON_CHOICES)
            turn = self.turn_set.create(year=Y, season=S)
            
        for g in self.government_set.all():
            uset = Unit.objects.filter(government=g)
            if S in ('S', 'F'):
                action = 'H'
            if S in ('SR', 'FR'):
                uset = uset.filter(displaced_from__isnull=False)
                action = 'M'
            if S == 'FA':
                builds = g.builds_available()
                if builds > 0:
                    for i in range(g.builds_available()):
                        turn.order_set.create(government=g,
                                              u_type=None,
                                              actor=None,
                                              action='B')
                    continue
                if builds == 0:
                    continue
                if builds < 0:
                    action = 'D'

            for u in uset:
                turn.order_set.create(government=g,
                                      u_type=u.u_type,
                                      actor=u.subregion,
                                      action=action)
    generate.alters_data = True

def game_changed(sender, **kwargs):
    created, instance = kwargs['created'], kwargs['instance']
    if created:
        convert = {'L': 'A', 'S': 'F'}
        for pwr in Power.objects.all():
            t_set = Territory.objects.filter(power=pwr)
            gvt = instance.government_set.create(name=pwr.name, power=pwr)
            gvt.owns.add(*list(t_set))
            for sr in Subregion.objects.filter(init_unit=True,
                                               territory__power=pwr):
                gvt.unit_set.create(u_type=convert[sr.sr_type],
                                    subregion=sr)
        instance.generate(start=True)
    else:
        if instance.state == 'A' and instance.turn_set.count() == 1:
            instance.generate()
post_save.connect(game_changed, sender=Game)

class Turn(models.Model):
    class Meta:
        get_latest_by = 'generated'
        ordering = ['-generated']
        
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
            return u'%s (%s)' % (self.territory.name, self.subname)
        else:
            return u'%s [%s]' % (self.territory.name, self.sr_type)

class Government(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(Power)
    owns = models.ManyToManyField(Territory, through='Ownership')

    def __unicode__(self):
        return self.name

    def supplycenters(self):
        return self.owns.filter(is_supply=True).count()

    def units(self):
        return Unit.objects.filter(government=self).count()

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
        # WARNING: the SQL standard says that nulls are not equal for
        #   uniqueness checks, however, some servers may not agree.
        unique_together = ("turn", "actor")
        
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
