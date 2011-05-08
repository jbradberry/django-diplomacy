import models, forms
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User

options = {'commit': False, 'verbosity': 0}

def create_units(units, turn, gvt):
    for fname, fsub in units.get('F', []):
        sr = models.Subregion.objects.get(
            sr_type='S', territory__name=fname, subname=fsub)
        models.Unit.objects.create(
            u_type='F', subregion=sr, turn=turn, government=gvt)
    for aname in units.get('A', []):
        sr = models.Subregion.objects.get(
            sr_type='L', territory__name=aname)
        models.Unit.objects.create(
            u_type='A', subregion=sr, turn=turn, government=gvt)


class CorrectnessHelperTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="tester")
        self.game = models.Game.objects.create(
            name="Test1", slug="test1", owner=self.owner, state='S')
        self.gvt = models.Government.objects.create(
            name="England", user=self.owner, game=self.game)
        self.turn = self.game.turn_set.create(number=0)
        self.game.state = 'A'
        self.game.save()

    def tearDown(self):
        self.owner.delete()
        self.game.delete()
        self.gvt.delete()
        self.turn.delete()

    def test_find_convoys(self):
        units = {'F': (('Mid-Atlantic Ocean', ''),
                       ('English Channel', ''),
                       ('Western Mediterranean', ''),
                       ('Spain', 'NC'),      # coastal, can't participate
                       ('Ionian Sea', ''),   # fake group
                       ('Adriatic Sea', ''), # fake group
                       ('Baltic Sea', ''),
                       ('Gulf of Bothnia', '')),
                 'A': ('Gascony', 'Sweden')}
        create_units(units, self.turn, self.gvt)
        legal = self.turn.find_convoys()

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


class BasicChecks(TestCase):
    """
    Based on section 6.A from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.A

    """

    fixtures = ['basic_game.json']

    def test_non_adjacent_move(self):
        # DATC 6.A.1
        call_command('loaddata', '6A1.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_move_army_to_sea(self):
        # DATC 6.A.2
        call_command('loaddata', '6A2.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_move_fleet_to_land(self):
        # DATC 6.A.3
        call_command('loaddata', '6A3.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector(self):
        # DATC 6.A.4
        call_command('loaddata', '6A4.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector_with_convoy(self):
        # DATC 6.A.5
        call_command('loaddata', '6A5.json', **options)

        T = models.Turn.objects.get()
        orders = models.Order.objects.values()

        for o in orders.filter(government__power__name='England'):
            self.assertTrue(not T.is_legal(o))

        for o in orders.filter(government__power__name='Germany'):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name='Yorkshire',
                              displaced_from__name='London').exists())

    def test_ordering_unit_of_another_country(self):
        # DATC 6.A.6
        call_command('loaddata', '6A6.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_only_armies_can_be_convoyed(self):
        # DATC 6.A.7
        call_command('loaddata', '6A7.json', **options)

        T = models.Turn.objects.get()
        orders = models.Order.objects.values()

        self.assertTrue(not T.is_legal(orders.get(slot=0)))
        self.assertTrue(not T.is_legal(orders.get(slot=1)))

    def test_support_to_hold_yourself(self):
        # DATC 6.A.8
        call_command('loaddata', '6A8.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get(
            government__power__name="Austria-Hungary")

        self.assertTrue(not T.is_legal(order))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name='Trieste',
                              displaced_from__name='Venice').exists())

    def test_fleets_must_follow_coast(self):
        # DATC 6.A.9
        call_command('loaddata', '6A9.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get()

        self.assertTrue(not T.is_legal(order))

    def test_support_on_unreachable_destination(self):
        # DATC 6.A.10
        call_command('loaddata', '6A10.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.values().get(
            actor__territory__name="Rome")

        self.assertTrue(not T.is_legal(order))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            not T.unit_set.filter(displaced_from__isnull=False).exists())

    def test_simple_bounce(self):
        # DATC 6.A.11
        call_command('loaddata', '6A11.json', **options)

        G = models.Game.objects.get()
        G.generate()
        T = G.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna").exists())
        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice").exists())
        self.assertEqual(
            T.unit_set.filter(standoff_from__name="Tyrolia").count(), 2)

    def test_bounce_of_three_units(self):
        # DATC 6.A.12
        call_command('loaddata', '6A12.json', **options)

        G = models.Game.objects.get()
        G.generate()
        T = G.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna").exists())
        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Munich").exists())
        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice").exists())

        self.assertEqual(T.unit_set.count(), 3)
        self.assertEqual(
            T.unit_set.filter(standoff_from__name="Tyrolia").count(), 3)
