from diplomacy import models
from collections import defaultdict

convert = {'L': 'A', 'S': 'F'}

class Setup(object):
    """
    Helper class to make setting up DATC tests much easier.
    
    """

    def __init__(self):
        self.index = 1
        self.u_index = 1
        self.gvt_index = defaultdict(int)
        self.sr = dict(("%s %s" % (convert[sr.sr_type], unicode(sr)), sr)
                       for sr in models.Subregion.objects.all())
        self.sr[None] = None
        models.Order.objects.all().delete()
        models.Unit.objects.all().delete()
        models.Turn.objects.exclude(number=0).delete()
        self.turn = models.Turn.objects.get()

    def new_turn(self):
        self.turn = models.Turn.objects.create(game=self.turn.game,
                                               number=self.turn.number+1)
        models.Turn.objects.filter(number=self.turn.number
                                   ).update(id=self.turn.number+1)
        self.turn.id = self.turn.number + 1

    def unit(self, gvt, subregion, displaced_from=None, standoff_from=None):
        gvt = models.Government.objects.get(power__name__istartswith=gvt)
        if displaced_from is not None:
            displaced_from = models.Territory.objects.get(name=displaced_from)
        if standoff_from is not None:
            standoff_from = models.Territory.objects.get(name=standoff_from)
        models.Unit.objects.create(id=self.u_index,
                                   turn=self.turn,
                                   government=gvt,
                                   u_type=convert[self.sr[subregion].sr_type],
                                   subregion=self.sr[subregion],
                                   displaced_from=displaced_from,
                                   standoff_from=standoff_from)
        self.u_index += 1

    def order(self, gvt, actor, action, assist, target, via_convoy=False):
        gvt = models.Government.objects.get(power__name__istartswith=gvt)
        if action != 'B' and '*' not in action:
            self.unit(gvt, actor)
        if '*' in action:
            action = action.strip('*')
        if target:
            sr = assist if assist else actor
            target = "%s %s" % (convert[self.sr[sr].sr_type], target)
        models.Order.objects.create(id=self.index,
                                    turn=self.turn,
                                    government=gvt,
                                    slot=self.gvt_index[gvt],
                                    actor=self.sr[actor],
                                    action=action,
                                    assist=self.sr[assist],
                                    target=self.sr[target],
                                    via_convoy=via_convoy)
        self.index += 1
        self.gvt_index[gvt] += 1
