from django.test import TestCase

from . import factories
from .helpers import create_units, create_orders
from .. import models


class CorrectnessHelperTest(TestCase):
    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in models.Power.objects.all()
        ]

        self.subs_unit = {
            models.subregion_key(s): "{0} {1}".format(models.convert[s.sr_type], unicode(s))
            for s in models.Subregion.objects.select_related('territory')
        }

    def test_find_convoys(self):
        units = {'England': ('F Mid-Atlantic Ocean',
                             'F English Channel',
                             'F Western Mediterranean',
                             'F Spain (NC)',   # coastal, can't participate
                             'F Ionian Sea',   # fake group
                             'F Adriatic Sea', # fake group
                             'F Baltic Sea',
                             'F Gulf of Bothnia',
                             'A Gascony',
                             'A Sweden')}
        T = models.Turn.objects.get()
        create_units(units, T)

        fleets = models.Subregion.objects.filter(
            sr_type='S', unit__turn=T
        ).exclude(territory__subregion__sr_type='L').distinct()
        fleets = [models.subregion_key(sr) for sr in fleets]
        legal = models.find_convoys(T.get_units(), fleets)

        self.assertEqual(len(legal), 2)
        (seas1, lands1), (seas2, lands2) = legal
        if len(seas1) == 2:
            seas1, seas2 = seas2, seas1
            lands1, lands2 = lands2, lands1

        self.assertEqual(len(seas1), 3)
        self.assertItemsEqual(
            [self.subs_unit[sr] for sr in seas1],
            units['England'][:3]
        )

        self.assertEqual(len(lands1), 10)
        self.assertItemsEqual(
            [sr[0] for sr in lands1],
            ['Tunisia', 'North Africa', 'London', 'Wales', 'Spain',
             'Brest', 'Gascony', 'Picardy', 'Belgium', 'Portugal']
        )

        self.assertEqual(len(seas2), 2)
        self.assertItemsEqual(
            [self.subs_unit[sr] for sr in seas2],
            units['England'][6:8]
        )

        self.assertEqual(len(lands2), 8)
        self.assertItemsEqual(
            [sr[0] for sr in lands2],
            ['Prussia', 'Berlin', 'Kiel', 'Denmark', 'Sweden',
             'Finland', 'St. Petersburg', 'Livonia']
        )
