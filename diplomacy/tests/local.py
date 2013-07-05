from .. import models
from .helpers import create_units, create_orders
from django.test import TestCase


unit_subs = dict(("{0} {1}".format(models.convert[s.sr_type], unicode(s)), s)
                  for s in models.Subregion.objects.select_related('territory'))
subs_unit = dict((v.id, k) for k,v in unit_subs.iteritems())


class CorrectnessHelperTest(TestCase):
    fixtures = ['basic_game.json']

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
        legal = T.find_convoys()

        full_sr = models.Subregion.objects.select_related('territory')

        self.assertEqual(len(legal), 2)
        (seas1, lands1), (seas2, lands2) = legal
        if len(seas1) == 2:
            seas1, seas2 = seas2, seas1
            lands1, lands2 = lands2, lands1

        self.assertEqual(len(seas1), 3)
        self.assertEqual(
            set(subs_unit[sr.id] for sr in full_sr.filter(id__in=seas1)),
            set(n for n in units['England'][:3]))

        self.assertEqual(len(lands1), 10)
        self.assertEqual(
            set(sr.territory.name for sr in full_sr.filter(id__in=lands1)),
            set(['Tunisia', 'North Africa', 'London', 'Wales', 'Spain',
                 'Brest', 'Gascony', 'Picardy', 'Belgium', 'Portugal']))

        self.assertEqual(len(seas2), 2)
        self.assertEqual(
            set(subs_unit[sr.id] for sr in full_sr.filter(id__in=seas2)),
            set(n for n in units['England'][6:8]))

        self.assertEqual(len(lands2), 8)
        self.assertEqual(
            set(sr.territory.name for sr in full_sr.filter(id__in=lands2)),
            set(['Prussia', 'Berlin', 'Kiel', 'Denmark', 'Sweden',
                 'Finland', 'St. Petersburg', 'Livonia']))
