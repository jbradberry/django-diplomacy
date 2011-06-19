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
        call_command('loaddata', '6A01.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_move_army_to_sea(self):
        # DATC 6.A.2
        call_command('loaddata', '6A02.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_move_fleet_to_land(self):
        # DATC 6.A.3
        call_command('loaddata', '6A03.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector(self):
        # DATC 6.A.4
        call_command('loaddata', '6A04.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector_with_convoy(self):
        # DATC 6.A.5
        call_command('loaddata', '6A05.json', **options)

        T = models.Turn.objects.get()
        orders = models.Order.objects.all()

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
        call_command('loaddata', '6A06.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_only_armies_can_be_convoyed(self):
        # DATC 6.A.7
        call_command('loaddata', '6A07.json', **options)

        T = models.Turn.objects.get()
        orders = models.Order.objects.all()

        self.assertTrue(not T.is_legal(orders.get(slot=0)))
        self.assertTrue(not T.is_legal(orders.get(slot=1)))

    def test_support_to_hold_yourself(self):
        # DATC 6.A.8
        call_command('loaddata', '6A08.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get(
            government__power__name="Austria-Hungary")

        self.assertTrue(not T.is_legal(order))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name='Trieste',
                              displaced_from__name='Venice').exists())

    def test_fleets_must_follow_coast(self):
        # DATC 6.A.9
        call_command('loaddata', '6A09.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_support_on_unreachable_destination(self):
        # DATC 6.A.10
        call_command('loaddata', '6A10.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get(
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


class CoastalIssues(TestCase):
    """
    Based on section 6.B from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.B

    """

    fixtures = ['basic_game.json']

    def test_move_to_unspecified_coast_when_necessary(self):
        # DATC 6.B.1

        # Note: this test is somewhat against the original intent,
        # since this implementation of Diplomacy uses entity selection
        # instead of string parsing for orders.
        call_command('loaddata', '6B01.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    #def test_move_to_unspecified_coast_when_unnecessary(self):
        # DATC 6.B.2

        # Note: this test would be entirely pointless as-is.  However,
        # if a text-parsing interface is ever implemented, it will be
        # necessary to test that.

    def test_moving_to_wrong_but_unnecessary_coast(self):
        # DATC 6.B.3

        # Note: this is another test which is checking something that
        # isn't a real problem.
        call_command('loaddata', '6B03.json', **options)

        T = models.Turn.objects.get()
        order = models.Order.objects.get()

        self.assertTrue(not T.is_legal(order))

    def test_support_to_unreachable_coast_allowed(self):
        # DATC 6.B.4
        call_command('loaddata', '6B04.json', **options)

        T = models.Turn.objects.get()

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              subregion__subname="NC",
                              government__power__name="France").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name=
                              "Western Mediterranean",
                              government__power__name="Italy").exists())

    def test_support_from_unreachable_coast_not_allowed(self):
        # DATC 6.B.5
        call_command('loaddata', '6B05.json', **options)

        T = models.Turn.objects.get()

        self.assertEqual(models.Order.objects.exclude(action='S').count(), 2)
        for o in models.Order.objects.exclude(action='S'):
            self.assertTrue(T.is_legal(o))

        o = models.Order.objects.get(action='S')
        self.assertTrue(not T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gulf of Lyon",
                              displaced_from__isnull=True,
                              government__power__name="Italy").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Marseilles",
                              government__power__name="France",
                              u_type='F').exists())

    def test_support_can_be_cut_from_other_coast(self):
        # DATC 6.B.6
        call_command('loaddata', '6B06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Mid-Atlantic Ocean",
                              displaced_from__name="North Atlantic Ocean"
                              ).exists())

    def test_coastal_crawl_not_allowed(self):
        # DATC 6.B.13
        call_command('loaddata', '6B13.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              subregion__subname='SC').exists())
        self.assertTrue(
            not T.unit_set.filter(subregion__territory__name="Bulgaria",
                                  subregion__subname='EC').exists())

    #def test_build_with_unspecified_coast(self):
        # DATC 6.B.14


class CircularMovement(TestCase):
    """
    Based on section 6.C from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.C

    """

    fixtures = ['basic_game.json']

    def test_three_unit_circular_move(self):
        # DATC 6.C.1
        call_command('loaddata', '6C01.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              u_type='A').exists())

    def test_three_unit_circular_move_with_support(self):
        # DATC 6.C.2
        call_command('loaddata', '6C02.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              u_type='A').exists())

    def test_disrupted_three_unit_circular_move(self):
        # DATC 6.C.3
        call_command('loaddata', '6C03.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              u_type='A').exists())

    def test_circular_move_with_attacked_convoy(self):
        # DATC 6.C.4
        call_command('loaddata', '6C04.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Turkey",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Serbia",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

    def test_circular_move_with_disrupted_convoy(self):
        # DATC 6.C.5
        call_command('loaddata', '6C05.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              u_type='F', government__power__name="Turkey",
                              displaced_from__isnull=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Serbia",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              government__power__name="Turkey",
                              u_type='A').exists())

    def test_two_armies_with_two_convoys(self):
        # DATC 6.C.6
        call_command('loaddata', '6C06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="France",
                              u_type='A').exists())

    def test_bounced_unit_swap(self):
        # DATC 6.C.7
        call_command('loaddata', '6C07.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Burgundy",
                              government__power__name="France",
                              u_type='A').exists())


class SupportsAndDislodges(TestCase):
    """
    Based on section 6.D from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.D

    """

    fixtures = ['basic_game.json']

    def test_supported_hold_prevents_dislodgement(self):
        # DATC 6.D.1
        call_command('loaddata', '6D01.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              displaced_from__isnull=True).exists())

    def test_move_cuts_support_on_hold(self):
        # DATC 6.D.2
        call_command('loaddata', '6D02.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              displaced_from__isnull=False).exists())

    def test_move_cuts_support_on_move(self):
        # DATC 6.D.3
        call_command('loaddata', '6D03.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

    def test_support_to_hold_on_unit_supporting_a_hold(self):
        # DATC 6.D.4
        call_command('loaddata', '6D04.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_support_to_hold_on_unit_supporting_a_move(self):
        # DATC 6.D.5
        call_command('loaddata', '6D05.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_support_to_hold_on_convoying_unit(self):
        # DATC 6.D.6
        call_command('loaddata', '6D06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Germany",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Livonia",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_support_to_hold_on_moving_unit(self):
        # DATC 6.D.7
        call_command('loaddata', '6D07.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Germany",
                              displaced_from__isnull=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_failed_convoyed_army_cannot_receive_hold_support(self):
        # DATC 6.D.8
        call_command('loaddata', '6D08.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Turkey",
                              displaced_from__isnull=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

    def test_support_to_move_on_holding_unit(self):
        # DATC 6.D.9
        call_command('loaddata', '6D09.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              displaced_from__isnull=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_self_dislodgement_prohibited(self):
        # DATC 6.D.10
        call_command('loaddata', '6D10.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            not T.unit_set.filter(subregion__territory__name="Berlin",
                                  u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              displaced_from__isnull=True,
                              u_type='A').exists())

    def test_no_self_dislodgement_of_returning_unit(self):
        # DATC 6.D.11
        call_command('loaddata', '6D11.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              displaced_from__isnull=True,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Warsaw",
                              u_type='A').exists())

    def test_support_foreign_unit_to_dislodge_own_unit(self):
        # DATC 6.D.12
        call_command('loaddata', '6D12.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_support_foreign_unit_to_dislodge_returning_own_unit(self):
        # DATC 6.D.13
        call_command('loaddata', '6D13.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_supporting_foreign_unit_insufficient_to_prevent_dislodge(self):
        # DATC 6.D.14
        call_command('loaddata', '6D14.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              displaced_from__isnull=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_defender_cannot_cut_support_for_attack_on_itself(self):
        # DATC 6.D.15
        call_command('loaddata', '6D15.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              displaced_from__isnull=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_convoying_a_unit_dislodging_a_unit_of_same_power(self):
        # DATC 6.D.16
        call_command('loaddata', '6D16.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              displaced_from__isnull=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="France",
                              u_type='A').exists())

    def test_dislodgement_cuts_supports(self):
        # DATC 6.D.17
        call_command('loaddata', '6D17.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              displaced_from__name="Ankara",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            not T.unit_set.filter(subregion__territory__name="Ankara"
                                  ).exists())

    def test_surviving_unit_will_sustain_support(self):
        # DATC 6.D.18
        call_command('loaddata', '6D18.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              displaced_from__name="Black Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_even_when_surviving_is_in_alternative_way(self):
        # DATC 6.D.19
        call_command('loaddata', '6D19.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              displaced_from__name="Black Sea",
                              u_type='F').exists())

    def test_unit_cannot_cut_support_of_its_own_country(self):
        # DATC 6.D.20
        call_command('loaddata', '6D20.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__name="North Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="England",
                              u_type='F').exists())

    def test_dislodging_does_not_cancel_support_cut(self):
        # DATC 6.D.21
        call_command('loaddata', '6D21.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Munich",
                              government__power__name="Germany",
                              displaced_from__name="Silesia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              displaced_from__isnull=True,
                              u_type='F').exists())

#     def test_impossible_fleet_move_cannot_be_supported(self):
#         # DATC 6.D.22
#         # parser test

    def test_impossible_coast_move_cannot_be_supported(self):
        # DATC 6.D.23
        call_command('loaddata', '6D23.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.filter(government__power__name=
                                             "France"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.filter(government__power__name=
                                             "Italy"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              government__power__name="France",
                              displaced_from__name="Gulf of Lyon",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              subregion__subname="SC",
                              government__power__name="Italy",
                              displaced_from__isnull=True).exists())

#     def test_impossible_army_move_cannot_be_supported(self):
#         # DATC 6.D.24
#         # parser test

    def test_failing_hold_support_can_be_supported(self):
        # DATC 6.D.25
        call_command('loaddata', '6D25.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())
