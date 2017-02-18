from django.test import TestCase

from . import factories
from .helpers import create_units, create_orders
from .. import models
from ..engine import standard
from ..engine.main import initialize_game
from ..engine.utils import get_territory
from ..models import is_legal


class BasicChecks(TestCase):
    """
    Based on section 6.A from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.A

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in standard.powers
        ]

    def test_non_adjacent_move(self):
        # DATC 6.A.1
        units = {"England": ("F North Sea",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea M Picardy",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_move_army_to_sea(self):
        # DATC 6.A.2
        units = {"England": ("A Liverpool",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Irish Sea",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_move_fleet_to_land(self):
        # DATC 6.A.3
        units = {"Germany": ("F Kiel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Kiel M Munich",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_move_to_own_sector(self):
        # DATC 6.A.4
        units = {"Germany": ("F Kiel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Kiel M Kiel",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_move_to_own_sector_with_convoy(self):
        # DATC 6.A.5
        units = {"England": ("F North Sea",
                             "A Yorkshire",
                             "A Liverpool"),
                 "Germany": ("F London",
                             "A Wales")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A Yorkshire - Yorkshire",
                              "A Yorkshire M Yorkshire",
                              "A Liverpool S A Yorkshire - Yorkshire"),
                  "Germany": ("F London M Yorkshire",
                              "A Wales S F London - Yorkshire")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        orders = models.Order.objects.all()

        for o in orders.filter(post__government__power__name='England'):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))

        for o in orders.filter(post__government__power__name='Germany'):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['displaced_from'])
                == ('yorkshire', 'london')
                for u in units))

    def test_ordering_unit_of_another_country(self):
        # DATC 6.A.6
        units = {"England": ("F London",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F London M North Sea",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_only_armies_can_be_convoyed(self):
        # DATC 6.A.7
        units = {"England": ("F London",
                             "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London M Belgium",
                              "F North Sea C F London - Belgium")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order1, order2 = models.Order.objects.all()

        self.assertFalse(is_legal(order1.as_data(), units, owns, T.season))
        self.assertFalse(is_legal(order2.as_data(), units, owns, T.season))

    def test_support_to_hold_yourself(self):
        # DATC 6.A.8
        units = {"Italy": ("A Venice",
                           "A Tyrolia"),
                 "Austria": ("F Trieste",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("A Venice M Trieste",
                            "A Tyrolia S A Venice - Trieste"),
                  "Austria": ("F Trieste S F Trieste",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get(
            post__government__power__name="Austria-Hungary")

        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['displaced_from'])
                == ('trieste', 'venice')
                for u in units))

    def test_fleets_must_follow_coast(self):
        # DATC 6.A.9
        units = {"Italy": ("F Rome",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("F Rome M Venice",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_support_on_unreachable_destination(self):
        # DATC 6.A.10
        units = {"Austria": ("A Venice",),
                 "Italy": ("F Rome",
                           "A Apulia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Venice H",),
                  "Italy": ("F Rome S A Apulia - Venice",
                            "A Apulia M Venice")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get(
            actor__territory__name="Rome")

        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertFalse(any(u['dislodged'] for u in units))

    def test_simple_bounce(self):
        # DATC 6.A.11
        units = {"Austria": ("A Vienna",),
                 "Italy": ("A Venice",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Vienna M Tyrolia",),
                  "Italy": ("A Venice M Tyrolia",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any(get_territory(u['subregion']) == 'vienna' for u in units))
        self.assertTrue(
            any(get_territory(u['subregion']) == 'venice' for u in units))
        self.assertEqual(
            sum(1 for u in units if u['standoff_from'] == 'tyrolia'), 2)

    def test_bounce_of_three_units(self):
        # DATC 6.A.12
        units = {"Austria": ("A Vienna",),
                 "Germany": ("A Munich",),
                 "Italy": ("A Venice",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Vienna M Tyrolia",),
                  "Germany": ("A Munich M Tyrolia",),
                  "Italy": ("A Venice M Tyrolia",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any(get_territory(u['subregion']) == 'vienna' for u in units))
        self.assertTrue(
            any(get_territory(u['subregion']) == 'munich' for u in units))
        self.assertTrue(
            any(get_territory(u['subregion']) == 'venice' for u in units))

        self.assertEqual(len(units), 3)
        self.assertEqual(
            sum(1 for u in units if u['standoff_from'] == 'tyrolia'), 3)


class CoastalIssues(TestCase):
    """
    Based on section 6.B from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.B

    Several of these tests are inverted, since the engine is stricter
    than specified by the DATC.

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in standard.powers
        ]

    def test_move_to_unspecified_coast_when_necessary(self):
        # DATC 6.B.1
        units = {"France": ("F Portugal",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Portugal M Spain",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    # expected fail
    def test_move_to_unspecified_coast_when_unnecessary(self):
        # DATC 6.B.2
        units = {"France": ("F Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Gascony M Spain",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        # self.assertTrue(is_legal(order.as_data(), units, owns, T.season))
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_moving_to_wrong_but_unnecessary_coast(self):
        # DATC 6.B.3
        units = {"France": ("F Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Gascony M Spain (SC)",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        order = models.Order.objects.get()
        self.assertFalse(is_legal(order.as_data(), units, owns, T.season))

    def test_support_to_unreachable_coast_allowed(self):
        # DATC 6.B.4
        units = {"France": ("F Gascony", "F Marseilles"),
                 "Italy": ("F Western Mediterranean",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Gascony M Spain (NC)",
                             "F Marseilles S F Gascony - Spain (NC)"),
                  "Italy": ("F Western Mediterranean M Spain (SC)",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((u['subregion'], u['government']) == ('spain.nc.s', 'france')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('western-mediterranean', 'italy')
                for u in units))

    def test_support_from_unreachable_coast_not_allowed(self):
        # DATC 6.B.5
        units = {"France": ("F Marseilles", "F Spain (NC)"),
                 "Italy": ("F Gulf of Lyon",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Marseilles M Gulf of Lyon",
                             "F Spain (NC) S F Marseilles - Gulf of Lyon"),
                  "Italy": ("F Gulf of Lyon H",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        self.assertEqual(models.Order.objects.exclude(action='S').count(), 2)
        for o in models.Order.objects.exclude(action='S'):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        o = models.Order.objects.get(action='S')
        self.assertFalse(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['government'])
                == ('gulf-of-lyon', False, 'italy')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('marseilles', 'france', 'F')
                for u in units))

    def test_support_can_be_cut_from_other_coast(self):
        # DATC 6.B.6
        units = {"England": ("F Irish Sea", "F North Atlantic Ocean"),
                 "France": ("F Spain (NC)", "F Mid-Atlantic Ocean"),
                 "Italy": ("F Gulf of Lyon",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Irish Sea S F North Atlantic Ocean - "
                              "Mid-Atlantic Ocean",
                              "F North Atlantic Ocean M Mid-Atlantic Ocean"),
                  "France": ("F Spain (NC) S F Mid-Atlantic Ocean",
                             "F Mid-Atlantic Ocean H"),
                  "Italy": ("F Gulf of Lyon M Spain (SC)",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['displaced_from'])
                == ('mid-atlantic-ocean', 'north-atlantic-ocean')
                for u in units))

    # expected fail
    def test_supporting_with_unspecified_coast(self):
        # DATC 6.B.7
        units = {"France": ("F Portugal", "F Mid-Atlantic Ocean"),
                 "Italy": ("F Gulf of Lyon", "F Western Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Portugal S F Mid-Atlantic Ocean - Spain",
                             "F Mid-Atlantic Ocean M Spain (NC)"),
                  "Italy": ("F Gulf of Lyon S F Western Mediterranean - "
                            "Spain (SC)",
                            "F Western Mediterranean M Spain (SC)")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        # for o in models.Order.objects.all():
        #     self.assertTrue(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(actor__territory__name=
                                              "Portugal"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        self.assertFalse(
            is_legal(models.Order.objects.get(actor__territory__name="Portugal").as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'mid-atlantic-ocean' for u in units)

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'western-mediterranean' for u in units)

        self.assertTrue(
            any((get_territory(u['subregion']), u['government']) == ('spain', 'italy')
                for u in units))

        self.assertTrue(
            any(get_territory(u['subregion']) == 'mid-atlantic-ocean'
                for u in units))

    # expected fail
    def test_supporting_with_unspecified_coast_when_only_one_possible(self):
        # DATC 6.B.8
        units = {"France": ("F Portugal", "F Gascony"),
                 "Italy": ("F Gulf of Lyon", "F Western Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Portugal S F Gascony - Spain",
                             "F Gascony M Spain (NC)"),
                  "Italy": ("F Gulf of Lyon S F Western Mediterranean - "
                            "Spain (SC)",
                            "F Western Mediterranean M Spain (SC)")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        # for o in models.Order.objects.all():
        #     self.assertTrue(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(actor__territory__name=
                                              "Portugal"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        self.assertFalse(
            is_legal(models.Order.objects.get(actor__territory__name="Portugal").as_data(),
                     units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'gascony' for u in units))

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'western-mediterranean' for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government']) == ('spain', 'italy')
                for u in units))

        self.assertTrue(
            any(get_territory(u['subregion']) == 'gascony' for u in units))

    # expected fail
    def test_supporting_with_wrong_coast(self):
        # DATC 6.B.9
        units = {"France": ("F Portugal", "F Mid-Atlantic Ocean"),
                 "Italy": ("F Gulf of Lyon", "F Western Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Portugal S F Mid-Atlantic Ocean - Spain (NC)",
                             "F Mid-Atlantic Ocean M Spain (SC)"),
                  "Italy": ("F Gulf of Lyon S F Western Mediterranean - "
                            "Spain (SC)",
                            "F Western Mediterranean M Spain (SC)")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'mid-atlantic-ocean' for u in units))

        # self.assertTrue(
        #     any(get_territory(u['subregion']) == 'western-mediterranean' for u in units))

        self.assertTrue(
            any(get_territory(u['subregion']) == 'mid-atlantic-ocean' for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('spain', 'italy')
                for u in units))

    # expected fail
    def test_unit_ordered_with_wrong_coast(self):
        # DATC 6.B.10
        units = {"France": ("F Spain (SC)",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Spain (NC) M Gulf of Lyon",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        o = models.Order.objects.get()
        # self.assertTrue(is_legal(o.as_data(), units, owns, T.season))
        self.assertFalse(is_legal(o.as_data(), units, owns, T.season))

    def test_coast_cannot_be_ordered_to_change(self):
        # DATC 6.B.11
        units = {"France": ("F Spain (NC)",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Spain (SC) M Gulf of Lyon",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        o = models.Order.objects.get()
        self.assertFalse(is_legal(o.as_data(), units, owns, T.season))

    # expected fail
    def test_army_movement_with_coastal_specification(self):
        # DATC 6.B.12
        units = {"France": ("A Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Gascony M Spain (NC)",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        o = models.Order.objects.get()
        # self.assertTrue(is_legal(o.as_data(), units, owns, T.season))
        self.assertFalse(is_legal(o.as_data(), units, owns, T.season))

    def test_coastal_crawl_not_allowed(self):
        # DATC 6.B.13
        units = {"Turkey": ("F Bulgaria (SC)", "F Constantinople")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Bulgaria (SC) M Constantinople",
                             "F Constantinople M Bulgaria (EC)")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(any(u['subregion'] == 'bulgaria.sc.s' for u in units))
        self.assertFalse(any(u['subregion'] == 'bulgaria.ec.s' for u in units))

    def test_build_with_unspecified_coast(self):
        # DATC 6.B.14
        T = models.Turn.objects.get()
        _, _, owns = initialize_game()
        T.create_ownership(owns)  # set up the proper ownership objects

        T.game.generate() # SR 1900
        T = T.game.current_turn()
        T.game.generate() # F 1900
        T = T.game.current_turn()
        T.game.generate() # FR 1900
        T = T.game.current_turn()
        T.game.generate() # FA 1900
        T = T.game.current_turn()

        orders = {"Russia": ("F St. Petersburg B",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        builds = models.builds_available(units, owns)
        self.assertEqual(builds.get('Russia', 0), 4)
        o = models.Order.objects.get()
        self.assertIsNone(o.actor)
        self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate() # S 1901
        T = T.game.current_turn()
        units = T.get_units()

        self.assertFalse(units)


class CircularMovement(TestCase):
    """
    Based on section 6.C from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.C

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in standard.powers
        ]

    def test_three_unit_circular_move(self):
        # DATC 6.C.1
        units = {"Turkey": ("F Ankara", "A Constantinople", "A Smyrna")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Ankara M Constantinople",
                             "A Constantinople M Smyrna",
                             "A Smyrna M Ankara")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('constantinople', 'ankara', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('smyrna', 'constantinople', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('ankara', 'smyrna', 'A')
                for u in units))

    def test_three_unit_circular_move_with_support(self):
        # DATC 6.C.2
        units = {"Turkey": ("F Ankara", "A Constantinople",
                            "A Smyrna", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Ankara M Constantinople",
                             "A Constantinople M Smyrna",
                             "A Smyrna M Ankara",
                             "A Bulgaria S F Ankara - Constantinople")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('constantinople', 'ankara', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('smyrna', 'constantinople', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('ankara', 'smyrna', 'A')
                for u in units))

    def test_disrupted_three_unit_circular_move(self):
        # DATC 6.C.3
        units = {"Turkey": ("F Ankara", "A Constantinople",
                            "A Smyrna", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Ankara M Constantinople",
                             "A Constantinople M Smyrna",
                             "A Smyrna M Ankara",
                             "A Bulgaria M Constantinople")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('ankara', 'ankara', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('constantinople', 'constantinople', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('smyrna', 'smyrna', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('bulgaria', 'bulgaria', 'A')
                for u in units))

    def test_circular_move_with_attacked_convoy(self):
        # DATC 6.C.4
        units = {"Austria": ("A Trieste", "A Serbia"),
                 "Turkey": ("A Bulgaria", "F Aegean Sea",
                            "F Ionian Sea", "F Adriatic Sea"),
                 "Italy": ("F Naples",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Trieste M Serbia",
                              "A Serbia M Bulgaria"),
                  "Turkey": ("A Bulgaria M Trieste",
                             "F Aegean Sea C A Bulgaria - Trieste",
                             "F Ionian Sea C A Bulgaria - Trieste",
                             "F Adriatic Sea C A Bulgaria - Trieste"),
                  "Italy": ("F Naples M Ionian Sea",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ionian-sea', 'turkey', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('trieste', 'turkey', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('serbia', 'trieste', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('bulgaria', 'austria-hungary', 'A')
                for u in units))

    def test_circular_move_with_disrupted_convoy(self):
        # DATC 6.C.5
        units = {"Austria": ("A Trieste", "A Serbia"),
                 "Turkey": ("A Bulgaria", "F Aegean Sea",
                            "F Ionian Sea", "F Adriatic Sea"),
                 "Italy": ("F Naples", "F Tunisia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Trieste M Serbia",
                              "A Serbia M Bulgaria"),
                  "Turkey": ("A Bulgaria M Trieste",
                             "F Aegean Sea C A Bulgaria - Trieste",
                             "F Ionian Sea C A Bulgaria - Trieste",
                             "F Adriatic Sea C A Bulgaria - Trieste"),
                  "Italy": ("F Naples M Ionian Sea",
                            "F Tunisia S F Naples - Ionian Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type'], u['government'], u['dislodged'])
                == ('ionian-sea', 'F', 'turkey', True)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('trieste', 'trieste', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('serbia', 'serbia', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('bulgaria', 'bulgaria', 'turkey', 'A')
                for u in units))

    def test_two_armies_with_two_convoys(self):
        # DATC 6.C.6
        units = {"England": ("F North Sea", "A London"),
                 "France": ("F English Channel", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "France": ("F English Channel C A Belgium - London",
                             "A Belgium M London")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'france', 'A')
                for u in units))

    def test_bounced_unit_swap(self):
        # DATC 6.C.7
        units = {"England": ("F North Sea", "A London"),
                 "France": ("F English Channel", "A Belgium", "A Burgundy")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "France": ("F English Channel C A Belgium - London",
                             "A Belgium M London",
                             "A Burgundy M Belgium")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('burgundy', 'france', 'A')
                for u in units))
