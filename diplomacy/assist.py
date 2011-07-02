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

    def order(self, gvt, actor, action, assist, target):
        gvt = models.Government.objects.get(power__name__istartswith=gvt)
        if action != 'B':
            models.Unit.objects.create(id=self.u_index,
                                       turn=self.turn,
                                       government=gvt,
                                       u_type=convert[self.sr[actor].sr_type],
                                       subregion=self.sr[actor])
            self.u_index += 1
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
                                    target=self.sr[target])
        self.index += 1
        self.gvt_index[gvt] += 1
