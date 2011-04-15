import unittest
import models, forms
from django.contrib.auth.models import User

def create_units(units, T):
    for fname, fsub in units['F']:
        sr = models.Subregion.objects.get(
            sr_type='S', territory__name=fname, subname=fsub)
        models.Unit.objects.create(
            u_type='F', subregion=sr, turn=T.turn, government=T.gvt)
    for aname in units['A']:
        sr = models.Subregion.objects.get(
            sr_type='L', territory__name=aname)
        models.Unit.objects.create(
            u_type='A', subregion=sr, turn=T.turn, government=T.gvt)


class CorrectnessHelperTest(unittest.TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="tester")
        self.game = models.Game.objects.create(
            name="Test1", slug="test1", owner=self.owner, state='S')
        self.gvt = models.Government.objects.create(
            name="England", user=self.owner, game=self.game)
        self.turn = self.game.turn_set.create(number=0)
        self.game.state = 'A'
        self.game.save()

    def test_legal_convoys(self):
        units = {'F': (('Mid-Atlantic Ocean', ''),
                       ('English Channel', ''),
                       ('Western Mediterranean', ''),
                       ('Spain', 'NC'),
                       ('Ionian Sea', ''),   # fake group
                       ('Adriatic Sea', ''), # fake group
                       ('Baltic Sea', ''),
                       ('Gulf of Bothnia', '')),
                 'A': ('Gascony', 'Sweden')}
        create_units(units, self)
        legal = forms.legal_convoys(self.turn)

        self.assertEqual(len(legal), 2)
        for seas, lands in legal:
            if len(seas) == 3:
                self.assertEqual(
                    set(sr.territory.name for sr in
                        models.Subregion.objects.filter(id__in=seas)),
                    set(n for n, s in units['F'][:3]))
                self.assertEqual(len(lands), 10)
                self.assertEqual(
                    set(sr.territory.name for sr in
                        models.Subregion.objects.filter(id__in=lands)),
                    set(['Tunisia', 'North Africa', 'London', 'Wales',
                         'Brest', 'Gascony', 'Picardy', 'Belgium', 'Portugal',
                         'Spain']))
            elif len(seas) == 2:
                self.assertEqual(
                    set(sr.territory.name for sr in
                        models.Subregion.objects.filter(id__in=seas)),
                    set(n for n, s in units['F'][6:]))
                self.assertEqual(len(lands), 8)
                self.assertEqual(
                    set(sr.territory.name for sr in
                        models.Subregion.objects.filter(id__in=lands)),
                    set(['Prussia', 'Berlin', 'Kiel', 'Denmark', 'Sweden',
                         'Finland', 'St. Petersburg', 'Livonia']))
            else:
                raise Exception("Didn't have the right number of seas.")
