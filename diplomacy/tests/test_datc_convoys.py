from django.test import TestCase

from . import factories
from .helpers import create_units, create_orders
from .. import models
from ..engine import standard
from ..engine.check import is_legal
from ..engine.utils import get_territory


class Convoys(TestCase):
    """
    Based on section 6.F from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.F

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = {
            pname: factories.GovernmentFactory(game=self.game, power=p)
            for p, pname in standard.powers.iteritems()
        }
        self.governments['Austria'] = self.governments['Austria-Hungary']

    def test_no_convoy_in_coastal_areas(self):
        # DATC 6.F.1
        units = {"Turkey": ("A Greece", "F Aegean Sea",
                            "F Constantinople", "F Black Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"Turkey": ("A Greece M Sevastopol",
                             "F Aegean Sea C A Greece - Sevastopol",
                             "F Constantinople C A Greece - Sevastopol",
                             "F Black Sea C A Greece - Sevastopol")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertFalse(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('greece', 'turkey', 'A')
                for u in units))

    def test_convoyed_army_can_bounce(self):
        # DATC 6.F.2
        units = {"England": ("F English Channel", "A London"),
                 "France": ("A Paris",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F English Channel C A London - Brest",
                              "A London M Brest"),
                  "France": ("A Paris M Brest",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('paris', 'france', 'A')
                for u in units))

    def test_convoyed_army_can_receive_support(self):
        # DATC 6.F.3
        units = {"England": ("F English Channel", "A London",
                             "F Mid-Atlantic Ocean"),
                 "France": ("A Paris",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F English Channel C A London - Brest",
                              "A London M Brest",
                              "F Mid-Atlantic Ocean S A London - Brest"),
                  "France": ("A Paris M Brest",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('brest', 'london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('paris', 'france', 'A')
                for u in units))

    def test_attacked_convoy_is_not_disrupted(self):
        # DATC 6.F.4
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Skagerrak",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Skagerrak M North Sea",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('holland', 'london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('skagerrak', 'germany', 'F')
                for u in units))

    def test_beleaguered_convoy_is_not_disrupted(self):
        # DATC 6.F.5
        units = {"England": ("F North Sea", "A London"),
                 "France": ("F English Channel", "F Belgium"),
                 "Germany": ("F Skagerrak", "F Denmark")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "France": ("F English Channel M North Sea",
                             "F Belgium S F English Channel - North Sea"),
                  "Germany": ("F Skagerrak M North Sea",
                              "F Denmark S F Skagerrak - North Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('holland', 'london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('english-channel', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('skagerrak', 'germany', 'F')
                for u in units))

    def test_dislodged_convoy_does_not_cut_support(self):
        # DATC 6.F.6
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("A Holland", "A Belgium",
                             "F Helgoland Bight", "F Skagerrak"),
                 "France": ("A Picardy", "A Burgundy")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("A Holland S A Belgium",
                              "A Belgium S A Holland",
                              "F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea"),
                  "France": ("A Picardy M Belgium",
                             "A Burgundy S A Picardy - Belgium")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'england', 'skagerrak', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'skagerrak', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('holland', 'germany', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'germany', 'A')
                for u in units))

    def test_dislodged_convoy_does_not_cause_contested_area(self):
        # DATC 6.F.7
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Helgoland Bight", "F Skagerrak")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'england', 'skagerrak', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'skagerrak', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        orders = {"England": ("F North Sea M Holland",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        order = T.get_orders()[0]
        self.assertTrue(is_legal(order, units, owns, T.season))

    def test_dislodged_convoy_does_not_cause_a_bounce(self):
        # DATC 6.F.8
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Helgoland Bight", "F Skagerrak", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea",
                              "A Belgium M Holland")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'england', 'skagerrak', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'skagerrak', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('holland', 'germany', 'A')
                for u in units))

    def test_dislodge_of_multi_route_convoy(self):
        # DATC 6.F.9
        units = {"England": ("F English Channel", "F North Sea", "A London"),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F English Channel C A London - Belgium",
                              "F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'england', 'mid-atlantic-ocean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'mid-atlantic-ocean', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

    def test_dislodge_of_multi_route_convoy_with_foreign_fleet(self):
        # DATC 6.F.10
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F English Channel",),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "Germany": ("F English Channel C A London - Belgium",),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'germany', 'mid-atlantic-ocean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'mid-atlantic-ocean', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

    def test_dislodge_of_multi_route_convoy_with_only_foreign_fleets(self):
        # DATC 6.F.11
        units = {"England": ("A London",),
                 "Germany": ("F English Channel",),
                 "Russia": ("F North Sea",),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A London M Belgium",),
                  "Germany": ("F English Channel C A London - Belgium",),
                  "Russia": ("F North Sea C A London - Belgium",),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'germany', 'mid-atlantic-ocean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'mid-atlantic-ocean', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

    def test_dislodged_convoying_fleet_not_on_route(self):
        # DATC 6.F.12
        units = {"England": ("F English Channel", "A London", "F Irish Sea"),
                 "France": ("F North Atlantic Ocean", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F English Channel C A London - Belgium",
                              "A London M Belgium",
                              "F Irish Sea C A London - Belgium"),
                  "France": ("F North Atlantic Ocean S F Mid-Atlantic Ocean"
                             " - Irish Sea",
                             "F Mid-Atlantic Ocean M Irish Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('irish-sea', 'england', 'mid-atlantic-ocean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('irish-sea', 'mid-atlantic-ocean', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

    def test_the_unwanted_alternative(self):
        # DATC 6.F.13
        units = {"England": ("A London", "F North Sea"),
                 "France": ("F English Channel",),
                 "Germany": ("F Holland", "F Denmark")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A London M Belgium",
                              "F North Sea C A London - Belgium"),
                  "France": ("F English Channel C A London - Belgium",),
                  "Germany": ("F Holland S F Denmark - North Sea",
                              "F Denmark M North Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'england', 'denmark', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'denmark', 'germany', 'F')
                for u in units))

    def test_simple_convoy_paradox(self):
        # DATC 6.F.14
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'france', 'wales', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'wales', 'england', 'F')
                for u in units))

    def test_simple_convoy_paradox_with_additional_convoy(self):
        # DATC 6.F.15
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel"),
                 "Italy": ("F Irish Sea", "F Mid-Atlantic Ocean",
                           "A North Africa")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Italy": ("F Irish Sea C A North Africa - Wales",
                            "F Mid-Atlantic Ocean C A North Africa - Wales",
                            "A North Africa M Wales")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'france', 'wales', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'wales', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('wales', 'italy', 'A')
                for u in units))

    def test_pandins_paradox(self):
        # DATC 6.F.16
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F North Sea", "F Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Germany": ("F North Sea S F Belgium - English Channel",
                              "F Belgium M English Channel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('wales', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('london', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('english-channel', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

    def test_pandins_extended_paradox(self):
        # DATC 6.F.17
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel", "F Yorkshire"),
                 "Germany": ("F North Sea", "F Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London",
                             "F Yorkshire S A Brest - London"),
                  "Germany": ("F North Sea S F Belgium - English Channel",
                              "F Belgium M English Channel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('wales', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('london', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('english-channel', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

    def test_betrayal_paradox(self):
        # DATC 6.F.18
        units = {"England": ("F North Sea", "A London", "F English Channel"),
                 "France": ("F Belgium",),
                 "Germany": ("F Helgoland Bight", "F Skagerrak")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium",
                              "F English Channel S A London - Belgium"),
                  "France": ("F Belgium S F North Sea",),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('skagerrak', 'germany', 'F')
                for u in units))

    def test_multi_route_convoy_disruption_paradox(self):
        # DATC 6.F.19
        units = {"France": ("A Tunisia", "F Tyrrhenian Sea", "F Ionian Sea"),
                 "Italy": ("F Naples", "F Rome")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"France": ("A Tunisia M Naples",
                             "F Tyrrhenian Sea C A Tunisia - Naples",
                             "F Ionian Sea C A Tunisia - Naples"),
                  "Italy": ("F Naples S F Rome - Tyrrhenian Sea",
                            "F Rome M Tyrrhenian Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('tyrrhenian-sea', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('naples', 'italy', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('rome', 'italy', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('tunisia', 'france', 'A')
                for u in units))

    def test_unwanted_multi_route_convoy_paradox(self):
        # DATC 6.F.20
        units = {"France": ("A Tunisia", "F Tyrrhenian Sea"),
                 "Italy": ("F Naples", "F Ionian Sea"),
                 "Turkey": ("F Aegean Sea", "F Eastern Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"France": ("A Tunisia M Naples",
                             "F Tyrrhenian Sea C A Tunisia - Naples"),
                  "Italy": ("F Naples S F Ionian Sea",
                            "F Ionian Sea C A Tunisia - Naples"),
                  "Turkey":
                      ("F Aegean Sea S F Eastern Mediterranean - Ionian Sea",
                       "F Eastern Mediterranean M Ionian Sea")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('ionian-sea', 'italy', 'eastern-mediterranean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('ionian-sea', 'eastern-mediterranean', 'turkey', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('tunisia', 'france', 'A')
                for u in units))

    def test_dads_army(self):
        # DATC 6.F.21
        units = {"Russia": ("A Edinburgh", "F Norwegian Sea", "A Norway"),
                 "France": ("F Irish Sea", "F Mid-Atlantic Ocean"),
                 "England": ("A Liverpool", "F North Atlantic Ocean",
                             "F Clyde")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"Russia": ("A Edinburgh S A Norway - Clyde",
                             "F Norwegian Sea C A Norway - Clyde",
                             "A Norway M Clyde"),
                  "France": ("F Irish Sea S F Mid-Atlantic Ocean"
                             " - North Atlantic Ocean",
                             "F Mid-Atlantic Ocean M North Atlantic Ocean"),
                  "England": ("A Liverpool M Clyde *", # via convoy
                              "F North Atlantic Ocean C A Liverpool - Clyde",
                              "F Clyde S F North Atlantic Ocean")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-atlantic-ocean', 'england', 'mid-atlantic-ocean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-atlantic-ocean', 'mid-atlantic-ocean', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('clyde', 'england', True, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('clyde', 'norway', 'russia', 'A')
                for u in units))

    def test_second_order_paradox_with_two_solutions(self):
        # DATC 6.F.22
        units = {"England": ("F Edinburgh", "F London"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F Belgium", "F Picardy"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F Edinburgh M North Sea",
                              "F London S F Edinburgh - North Sea"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Germany": ("F Belgium S F Picardy - English Channel",
                              "F Picardy M English Channel"),
                  "Russia": ("A Norway M Belgium",
                             "F North Sea C A Norway - Belgium")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'france', 'picardy', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'picardy', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'russia', 'edinburgh', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'edinburgh', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'russia', 'A')
                for u in units))

    def test_second_order_paradox_with_two_exclusive_convoys(self):
        # DATC 6.F.23
        units = {"England": ("F Edinburgh", "F Yorkshire"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F Belgium", "F London"),
                 "Italy": ("F Mid-Atlantic Ocean", "F Irish Sea"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F Edinburgh M North Sea",
                              "F Yorkshire S F Edinburgh - North Sea"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Germany": ("F Belgium S F English Channel",
                              "F London S F North Sea"),
                  "Italy":
                      ("F Mid-Atlantic Ocean M English Channel",
                       "F Irish Sea S F Mid-Atlantic Ocean - English Channel"),
                  "Russia": ("A Norway M Belgium",
                             "F North Sea C A Norway - Belgium")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'russia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('english-channel', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('mid-atlantic-ocean', 'italy', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'russia', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('edinburgh', 'england', 'F')
                for u in units))

    def test_second_order_paradox_with_no_resolution(self):
        # DATC 6.F.24
        units = {"England": ("F Edinburgh", "F London", "F Irish Sea",
                             "F Mid-Atlantic Ocean"),
                 "France": ("A Brest", "F English Channel", "F Belgium"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England":
                      ("F Edinburgh M North Sea",
                       "F London S F Edinburgh - North Sea",
                       "F Irish Sea M English Channel",
                       "F Mid-Atlantic Ocean S F Irish Sea - English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London",
                             "F Belgium S F English Channel"),
                  "Russia": ("A Norway M Belgium",
                             "F North Sea C A Norway - Belgium")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('brest', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'russia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('english-channel', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('irish-sea', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'russia', 'edinburgh', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('north-sea', 'edinburgh', 'england', 'F')
                for u in units))


class ConvoyingToAdjacent(TestCase):
    """
    Based on section 6.G from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.G

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = {
            pname: factories.GovernmentFactory(game=self.game, power=p)
            for p, pname in standard.powers.iteritems()
        }
        self.governments['Austria'] = self.governments['Austria-Hungary']

    def test_two_units_can_swap_by_convoy(self):
        # DATC 6.G.1
        units = {"England": ("A Norway", "F Skagerrak"),
                 "Russia": ("A Sweden",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden",
                              "F Skagerrak C A Norway - Sweden"),
                  "Russia": ("A Sweden M Norway",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('norway', 'sweden', 'russia', 'A')
                for u in units))

    def test_kidnapping_an_army(self):
        # DATC 6.G.2
        units = {"England": ("A Norway",),
                 "Russia": ("F Sweden",),
                 "Germany": ("F Skagerrak",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden",),
                  "Russia": ("F Sweden M Norway",),
                  "Germany": ("F Skagerrak C A Norway - Sweden",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('sweden', 'russia', 'F')
                for u in units))

    def test_kidnapping_with_disrupted_convoy(self):
        # DATC 6.G.3
        units = {"France": ("F Brest", "A Picardy", "A Burgundy",
                            "F Mid-Atlantic Ocean"),
                 "England": ("F English Channel",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"France":
                      ("F Brest M English Channel",
                       "A Picardy M Belgium",
                       "A Burgundy S A Picardy - Belgium",
                       "F Mid-Atlantic Ocean S F Brest - English Channel"),
                  "England": ("F English Channel C A Picardy - Belgium",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('belgium', 'picardy', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'england', 'brest', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'brest', 'france', 'F')
                for u in units))

    def test_kidnapping_with_disrupted_convoy_and_opposite_move(self):
        # DATC 6.G.4
        units = {"France": ("F Brest", "A Picardy", "A Burgundy",
                            "F Mid-Atlantic Ocean"),
                 "England": ("F English Channel", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"France":
                      ("F Brest M English Channel",
                       "A Picardy M Belgium",
                       "A Burgundy S A Picardy - Belgium",
                       "F Mid-Atlantic Ocean S F Brest - English Channel"),
                 "England": ("F English Channel C A Picardy - Belgium",
                             "A Belgium M Picardy")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('belgium', 'picardy', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'england', 'brest', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'brest', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('belgium', 'england', 'picardy', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('belgium', 'picardy', 'france', 'A')
                for u in units))

    def test_swapping_with_intent(self):
        # DATC 6.G.5
        units = {"Italy": ("A Rome", "F Tyrrhenian Sea"),
                 "Turkey": ("A Apulia", "F Ionian Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"Italy": ("A Rome M Apulia",
                            "F Tyrrhenian Sea C A Apulia - Rome"),
                  "Turkey": ("A Apulia M Rome",
                             "F Ionian Sea C A Apulia - Rome")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('apulia', 'rome', 'italy', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('rome', 'apulia', 'turkey', 'A')
                for u in units))

    def test_swapping_with_unintended_intent(self):
        # DATC 6.G.6
        units = {"England": ("A Liverpool", "F English Channel"),
                 "Germany": ("A Edinburgh",),
                 "France": ("F Irish Sea", "F North Sea"),
                 "Russia": ("F Norwegian Sea", "F North Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Liverpool M Edinburgh",
                              "F English Channel C A Liverpool - Edinburgh"),
                  "Germany": ("A Edinburgh M Liverpool",),
                  "France": ("F Irish Sea H",
                             "F North Sea H"),
                  "Russia":
                      ("F Norwegian Sea C A Liverpool - Edinburgh",
                       "F North Atlantic Ocean C A Liverpool - Edinburgh")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('edinburgh', 'liverpool', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('liverpool', 'edinburgh', 'germany', 'A')
                for u in units))

    def test_swapping_with_illegal_intent(self):
        # DATC 6.G.7
        units = {"England": ("F Skagerrak", "F Norway"),
                 "Russia": ("A Sweden", "F Gulf of Bothnia")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F Skagerrak C A Sweden - Norway",
                              "F Norway M Sweden"),
                  "Russia": ("A Sweden M Norway",
                             "F Gulf of Bothnia C A Sweden - Norway")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            if get_territory(o['actor']) != 'gulf-of-bothnia':
                self.assertTrue(is_legal(o, units, owns, T.season))
            else:
                self.assertFalse(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('sweden', 'russia', 'A')
                for u in units))

    def test_explicit_convoy_that_isnt_there(self):
        # DATC 6.G.8
        units = {"France": ("A Belgium",),
                 "England": ("F North Sea", "A Holland")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"France": ("A Belgium M Holland *",), # via convoy
                  "England": ("F North Sea M Helgoland Bight",
                              "A Holland M Kiel")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('holland', 'belgium', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('kiel', 'holland', 'england', 'A')
                for u in units))

    def test_swapped_or_dislodged(self):
        # DATC 6.G.9
        units = {"England": ("A Norway", "F Skagerrak", "F Finland"),
                 "Russia": ("A Sweden",)}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden",
                              "F Skagerrak C A Norway - Sweden",
                              "F Finland S A Norway - Sweden"),
                  "Russia": ("A Sweden M Norway",)}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'],
                 u['dislodged'], u['u_type']) == ('norway', 'sweden', 'russia', False, 'A')
                for u in units))

    def test_swapped_or_head_to_head(self):
        # DATC 6.G.10
        units = {"England": ("A Norway", "F Denmark", "F Finland"),
                 "Germany": ("F Skagerrak",),
                 "Russia": ("A Sweden", "F Barents Sea"),
                 "France": ("F Norwegian Sea", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden *", # via convoy
                              "F Denmark S A Norway - Sweden",
                              "F Finland S A Norway - Sweden"),
                  "Germany": ("F Skagerrak C A Norway - Sweden",),
                  "Russia": ("A Sweden M Norway",
                             "F Barents Sea S A Sweden - Norway"),
                  "France": ("F Norwegian Sea M Norway",
                             "F North Sea S F Norwegian Sea - Norway")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('sweden', 'russia', True, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norwegian-sea', 'france', 'F')
                for u in units))

    def test_convoy_to_adjacent_place_with_paradox(self):
        # DATC 6.G.11
        units = {"England": ("F Norway", "F North Sea"),
                 "Russia": ("A Sweden", "F Skagerrak", "F Barents Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F Norway S F North Sea - Skagerrak",
                              "F North Sea M Skagerrak"),
                  "Russia": ("A Sweden M Norway",
                             "F Skagerrak C A Sweden - Norway",
                             "F Barents Sea S A Sweden - Norway")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('skagerrak', 'north-sea', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('skagerrak', 'russia', 'north-sea', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('sweden', 'russia', 'A')
                for u in units))

    def test_swapping_two_units_with_two_convoys(self):
        # DATC 6.G.12
        units = {"England": ("A Liverpool", "F North Atlantic Ocean",
                             "F Norwegian Sea"),
                 "Germany": ("A Edinburgh", "F North Sea",
                             "F English Channel", "F Irish Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England":
                      ("A Liverpool M Edinburgh *", # via convoy
                       "F North Atlantic Ocean C A Liverpool - Edinburgh",
                       "F Norwegian Sea C A Liverpool - Edinburgh"),
                  "Germany": ("A Edinburgh M Liverpool *", # via convoy
                              "F North Sea C A Edinburgh - Liverpool",
                              "F English Channel C A Edinburgh - Liverpool",
                              "F Irish Sea C A Edinburgh - Liverpool")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('edinburgh', 'liverpool', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('liverpool', 'edinburgh', 'germany', 'A')
                for u in units))

    def test_support_cut_on_attack_on_itself_via_convoy(self):
        # DATC 6.G.13
        units = {"Austria": ("F Adriatic Sea", "A Trieste"),
                 "Italy": ("A Venice", "F Albania")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"Austria": ("F Adriatic Sea C A Trieste - Venice",
                              "A Trieste M Venice *"), # via convoy
                  "Italy": ("A Venice S F Albania - Trieste",
                            "F Albania M Trieste")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('trieste', 'austria-hungary', 'albania', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('trieste', 'albania', 'italy', 'F')
                for u in units))

    def test_bounce_by_convoy_to_adjacent_place(self):
        # DATC 6.G.14
        units = {"England": ("A Norway", "F Denmark", "F Finland"),
                 "France": ("F Norwegian Sea", "F North Sea"),
                 "Germany": ("F Skagerrak",),
                 "Russia": ("A Sweden", "F Barents Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden",
                              "F Denmark S A Norway - Sweden",
                              "F Finland S A Norway - Sweden"),
                  "France": ("F Norwegian Sea M Norway",
                             "F North Sea S F Norwegian Sea - Norway"),
                  "Germany": ("F Skagerrak C A Sweden - Norway",),
                  "Russia": ("A Sweden M Norway *", # via convoy
                             "F Barents Sea S A Sweden - Norway"),
                  }
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('sweden', 'russia', 'norway', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norwegian-sea', 'france', 'F')
                for u in units))

    def test_bounce_and_dislodge_with_double_convoy(self):
        # DATC 6.G.15
        units = {"England": ("F North Sea", "A Holland",
                             "A Yorkshire", "A London"),
                 "France": ("F English Channel", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A Holland S A London - Belgium",
                              "A Yorkshire M London",
                              "A London M Belgium *"), # via convoy
                  "France": ("F English Channel C A Belgium - London",
                             "A Belgium M London *")} # via convoy
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('belgium', 'london', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('belgium', 'france', True, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('yorkshire', 'england', 'A')
                for u in units))

    def test_two_units_in_one_area_bug_by_convoy(self):
        # DATC 6.G.16
        units = {"England": ("A Norway", "A Denmark",
                             "F Baltic Sea", "F North Sea"),
                 "Russia": ("A Sweden", "F Skagerrak", "F Norwegian Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden",
                              "A Denmark S A Norway - Sweden",
                              "F Baltic Sea S A Norway - Sweden",
                              "F North Sea M Norway"),
                  "Russia": ("A Sweden M Norway *", # via convoy
                             "F Skagerrak C A Sweden - Norway",
                             "F Norwegian Sea S A Sweden - Norway")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertEqual(
            sum(1 for u in units if get_territory(u['subregion']) == 'norway'), 1)

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('norway', 'sweden', 'russia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('north-sea', 'england', 'F')
                for u in units))

    def test_two_units_in_one_area_bug_moving_over_land(self):
        # DATC 6.G.17
        units = {"England": ("A Norway", "A Denmark", "F Baltic Sea",
                             "F Skagerrak", "F North Sea"),
                 "Russia": ("A Sweden", "F Norwegian Sea")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("A Norway M Sweden *", # via convoy
                              "A Denmark S A Norway - Sweden",
                              "F Baltic Sea S A Norway - Sweden",
                              "F Skagerrak C A Norway - Sweden",
                              "F North Sea M Norway"),
                  "Russia": ("A Sweden M Norway",
                             "F Norwegian Sea S A Sweden - Norway")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('sweden', 'norway', 'england', 'A')
                for u in units))

        self.assertEqual(
            sum(1 for u in units if get_territory(u['subregion']) == 'norway'), 1)

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('norway', 'sweden', 'russia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('north-sea', 'england', 'F')
                for u in units))

    def test_two_units_in_one_area_bug_with_double_convoy(self):
        # DATC 6.G.18
        units = {"England": ("F North Sea", "A Holland", "A Yorkshire",
                             "A London", "A Ruhr"),
                 "France": ("F English Channel", "A Belgium", "A Wales")}
        T = models.Turn.objects.get()
        create_units(units, T, self.governments)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A Holland S A London - Belgium",
                              "A Yorkshire M London",
                              "A London M Belgium",
                              "A Ruhr S A London - Belgium"),
                  "France": ("F English Channel C A Belgium - London",
                             "A Belgium M London",
                             "A Wales S A Belgium - London")}
        create_orders(orders, T, self.governments)

        units = T.get_units()
        owns = T.get_ownership()
        orders = T.get_orders()
        for o in orders:
            self.assertTrue(is_legal(o, units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('belgium', 'london', 'england', 'A')
                for u in units))

        self.assertEqual(
            sum(1 for u in units if get_territory(u['subregion']) == 'london'), 1)

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('london', 'belgium', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('yorkshire', 'england', 'A')
                for u in units))
