from django.test import TestCase

from . import factories
from .helpers import create_units, create_orders
from .. import models
from ..engine import standard
from ..engine.utils import get_territory
from ..models import is_legal


class SupportsAndDislodges(TestCase):
    """
    Based on section 6.D from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.D

    """

    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in standard.powers
        ]

    def test_supported_hold_prevents_dislodgement(self):
        # DATC 6.D.1
        units = {"Austria": ("F Adriatic Sea", "A Trieste"),
                 "Italy": ("A Venice", "A Tyrolia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Adriatic Sea S A Trieste - Venice",
                              "A Trieste M Venice"),
                  "Italy": ("A Venice H",
                            "A Tyrolia S A Venice")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('venice', 'italy', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('trieste', 'austria-hungary')
                for u in units))

    def test_move_cuts_support_on_hold(self):
        # DATC 6.D.2
        units = {"Austria": ("F Adriatic Sea", "A Trieste", "A Vienna"),
                 "Italy": ("A Venice", "A Tyrolia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Adriatic Sea S A Trieste - Venice",
                              "A Trieste M Venice",
                              "A Vienna M Tyrolia"),
                  "Italy": ("A Venice H",
                            "A Tyrolia S A Venice")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('venice', 'italy', True)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('venice', 'austria-hungary')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('vienna', 'austria-hungary')
                for u in units))

    def test_move_cuts_support_on_move(self):
        # DATC 6.D.3
        units = {"Austria": ("F Adriatic Sea", "A Trieste"),
                 "Italy": ("A Venice", "F Ionian Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Adriatic Sea S A Trieste - Venice",
                              "A Trieste M Venice"),
                  "Italy": ("A Venice H",
                            "F Ionian Sea M Adriatic Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('venice', 'italy', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('ionian-sea', 'italy')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('trieste', 'austria-hungary')
                for u in units))

    def test_support_to_hold_on_unit_supporting_a_hold(self):
        # DATC 6.D.4
        units = {"Germany": ("A Berlin", "F Kiel"),
                 "Russia": ("F Baltic Sea", "A Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin S F Kiel",
                              "F Kiel S A Berlin"),
                  "Russia": ("F Baltic Sea S A Prussia - Berlin",
                             "A Prussia M Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('berlin', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'russia', 'A')
                for u in units))

    def test_support_to_hold_on_unit_supporting_a_move(self):
        # DATC 6.D.5
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich"),
                 "Russia": ("F Baltic Sea", "A Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin S A Munich - Silesia",
                              "F Kiel S A Berlin",
                              "A Munich M Silesia"),
                  "Russia": ("F Baltic Sea S A Prussia - Berlin",
                             "A Prussia M Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('berlin', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'russia', 'A')
                for u in units))

    def test_support_to_hold_on_convoying_unit(self):
        # DATC 6.D.6
        units = {"Germany": ("A Berlin", "F Baltic Sea", "F Prussia"),
                 "Russia": ("F Livonia", "F Gulf of Bothnia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Sweden",
                              "F Baltic Sea C A Berlin - Sweden",
                              "F Prussia S F Baltic Sea"),
                  "Russia": ("F Livonia M Baltic Sea",
                             "F Gulf of Bothnia S F Livonia - Baltic Sea")}
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
                == ('sweden', 'germany', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('baltic-sea', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('livonia', 'russia', 'F')
                for u in units))

    def test_support_to_hold_on_moving_unit(self):
        # DATC 6.D.7
        units = {"Germany": ("F Baltic Sea", "F Prussia"),
                 "Russia": ("F Livonia", "F Gulf of Bothnia", "A Finland")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Baltic Sea M Sweden",
                              "F Prussia S F Baltic Sea"),
                  "Russia": ("F Livonia M Baltic Sea",
                             "F Gulf of Bothnia S F Livonia - Baltic Sea",
                             "A Finland M Sweden")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('baltic-sea', 'germany', True)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('baltic-sea', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'])
                == ('finland', 'russia')
                for u in units))

    def test_failed_convoyed_army_cannot_receive_hold_support(self):
        # DATC 6.D.8
        units = {"Austria": ("F Ionian Sea", "A Serbia", "A Albania"),
                 "Turkey": ("A Greece", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Ionian Sea H",
                              "A Serbia S A Albania - Greece",
                              "A Albania M Greece"),
                  "Turkey": ("A Greece M Naples",
                             "A Bulgaria S A Greece")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('greece', 'turkey', True)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('greece', 'austria-hungary', 'A')
                for u in units))

    def test_support_to_move_on_holding_unit(self):
        # DATC 6.D.9
        units = {"Italy": ("A Venice", "A Tyrolia"),
                 "Austria": ("A Albania", "A Trieste")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("A Venice M Trieste",
                            "A Tyrolia S A Venice - Trieste"),
                  "Austria": ("A Albania S A Trieste - Serbia",
                              "A Trieste H")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('trieste', 'austria-hungary', True)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('trieste', 'italy', 'A')
                for u in units))

    def test_self_dislodgement_prohibited(self):
        # DATC 6.D.10
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin H",
                              "F Kiel M Berlin",
                              "A Munich S F Kiel - Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['u_type'])
                == ('berlin', False, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('kiel', 'F')
                for u in units))

    def test_no_self_dislodgement_of_returning_unit(self):
        # DATC 6.D.11
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich"),
                 "Russia": ("A Warsaw",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Prussia",
                              "F Kiel M Berlin",
                              "A Munich S F Kiel - Berlin"),
                  "Russia": ("A Warsaw M Prussia",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['u_type'])
                == ('berlin', False, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('kiel', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('warsaw', 'A')
                for u in units))

    def test_support_foreign_unit_to_dislodge_own_unit(self):
        # DATC 6.D.12
        units = {"Austria": ("F Trieste", "A Vienna"),
                 "Italy": ("A Venice",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Trieste H",
                              "A Vienna S A Venice - Trieste"),
                  "Italy": ("A Venice M Trieste",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['u_type'])
                == ('trieste', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('venice', 'A')
                for u in units))

    def test_support_foreign_unit_to_dislodge_returning_own_unit(self):
        # DATC 6.D.13
        units = {"Austria": ("F Trieste", "A Vienna"),
                 "Italy": ("A Venice", "F Apulia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Trieste M Adriatic Sea",
                              "A Vienna S A Venice - Trieste"),
                  "Italy": ("A Venice M Trieste",
                            "F Apulia M Adriatic Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['u_type'])
                == ('trieste', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('venice', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('apulia', 'F')
                for u in units))

    def test_supporting_foreign_unit_insufficient_to_prevent_dislodge(self):
        # DATC 6.D.14
        units = {"Austria": ("F Trieste", "A Vienna"),
                 "Italy": ("A Venice", "A Tyrolia", "F Adriatic Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Trieste H",
                              "A Vienna S A Venice - Trieste"),
                  "Italy": ("A Venice M Trieste",
                            "A Tyrolia S A Venice - Trieste",
                            "F Adriatic Sea S A Venice - Trieste")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['dislodged'], u['u_type'])
                == ('trieste', True, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['u_type'])
                == ('trieste', 'venice', 'A')
                for u in units))

    def test_defender_cannot_cut_support_for_attack_on_itself(self):
        # DATC 6.D.15
        units = {"Russia": ("F Constantinople", "F Black Sea"),
                 "Turkey": ("F Ankara",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Constantinople S F Black Sea - Ankara",
                             "F Black Sea M Ankara"),
                  "Turkey": ("F Ankara M Constantinople",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('ankara', 'turkey', True, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ankara', 'russia', 'F')
                for u in units))

    def test_convoying_a_unit_dislodging_a_unit_of_same_power(self):
        # DATC 6.D.16
        units = {"England": ("A London", "F North Sea"),
                 "France": ("F English Channel", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A London H",
                              "F North Sea C A Belgium - London"),
                  "France": ("F English Channel S A Belgium - London",
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
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('london', 'england', True, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('london', 'france', 'A')
                for u in units))

    def test_dislodgement_cuts_supports(self):
        # DATC 6.D.17
        units = {"Russia": ("F Constantinople", "F Black Sea"),
                 "Turkey": ("F Ankara", "A Smyrna", "A Armenia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Constantinople S F Black Sea - Ankara",
                             "F Black Sea M Ankara"),
                  "Turkey": ("F Ankara M Constantinople",
                             "A Smyrna S F Ankara - Constantinople",
                             "A Armenia M Ankara")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('constantinople', 'russia', 'ankara', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('constantinople', 'ankara', 'turkey', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('black-sea', 'russia', 'F')
                for u in units))

    def test_surviving_unit_will_sustain_support(self):
        # DATC 6.D.18
        units = {"Russia": ("F Constantinople", "F Black Sea", "A Bulgaria"),
                 "Turkey": ("F Ankara", "A Smyrna", "A Armenia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Constantinople S F Black Sea - Ankara",
                             "F Black Sea M Ankara",
                             "A Bulgaria S F Constantinople"),
                  "Turkey": ("F Ankara M Constantinople",
                             "A Smyrna S F Ankara - Constantinople",
                             "A Armenia M Ankara")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('constantinople', 'russia', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('ankara', 'turkey', 'black-sea', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('ankara', 'black-sea', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('armenia', 'A')
                for u in units))

    def test_even_when_surviving_is_in_alternative_way(self):
        # DATC 6.D.19
        units = {"Russia": ("F Constantinople", "F Black Sea", "A Smyrna"),
                 "Turkey": ("F Ankara",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Constantinople S F Black Sea - Ankara",
                             "F Black Sea M Ankara",
                             "A Smyrna S F Ankara - Constantinople"),
                  "Turkey": ("F Ankara M Constantinople",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('constantinople', 'russia', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('ankara', 'black-sea', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('ankara', 'turkey', 'black-sea', 'F')
                for u in units))

    def test_unit_cannot_cut_support_of_its_own_country(self):
        # DATC 6.D.20
        units = {"England": ("F London", "F North Sea", "A Yorkshire"),
                 "France": ("F English Channel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London S F North Sea - English Channel",
                              "F North Sea M English Channel",
                              "A Yorkshire M London"),
                  "France": ("F English Channel H",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['u_type']) == ('yorkshire', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('english-channel', 'france', 'north-sea', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('english-channel', 'north-sea', 'england', 'F')
                for u in units))

    def test_dislodging_does_not_cancel_support_cut(self):
        # DATC 6.D.21
        units = {"Austria": ("F Trieste",),
                 "Italy": ("A Venice", "A Tyrolia"),
                 "Germany": ("A Munich",),
                 "Russia": ("A Silesia", "A Berlin")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Trieste H",),
                  "Italy": ("A Venice M Trieste",
                            "A Tyrolia S A Venice - Trieste"),
                  "Germany": ("A Munich M Tyrolia",),
                  "Russia": ("A Silesia M Munich",
                             "A Berlin S A Silesia - Munich")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('munich', 'germany', 'silesia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('munich', 'silesia', 'russia', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('vencie', 'italy', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('trieste', 'austria-hungary', False, 'F')
                for u in units))

    def test_impossible_fleet_move_cannot_be_supported(self):
        # DATC 6.D.22
        units = {"Germany": ("F Kiel", "A Burgundy"),
                 "Russia": ("A Munich", "A Berlin")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Kiel M Munich",
                              "A Burgundy S F Kiel - Munich"),
                  "Russia": ("A Munich M Kiel",
                             "A Berlin S A Munich - Kiel")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Germany"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('kiel', 'germany', 'munich', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'])
                == ('kiel', 'munich', 'russia')
                for u in units))

    def test_impossible_coast_move_cannot_be_supported(self):
        # DATC 6.D.23
        units = {"Italy": ("F Gulf of Lyon", "F Western Mediterranean"),
                 "France": ("F Spain (NC)", "F Marseilles")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("F Gulf of Lyon M Spain (SC)",
                            "F Western Mediterranean S F Gulf of Lyon"
                            " - Spain (SC)"),
                  "France": ("F Spain (NC) M Gulf of Lyon",
                             "F Marseilles S F Spain (NC) - Gulf of Lyon")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "France"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Italy"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('spain', 'france', 'gulf-of-lyon', 'F')
                for u in units))

        self.assertTrue(
            any((u['subregion'], u['government']) == ('spain.sc.s', 'italy')
                for u in units))

    def test_impossible_army_move_cannot_be_supported(self):
        # DATC 6.D.24
        units = {"France": ("A Marseilles", "F Spain (SC)"),
                 "Italy": ("F Gulf of Lyon",),
                 "Turkey": ("F Tyrrhenian Sea", "F Western Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Marseilles M Gulf of Lyon",
                             "F Spain (SC) S A Marseilles - Gulf of Lyon"),
                  "Italy": ("F Gulf of Lyon H",),
                  "Turkey": ("F Tyrrhenian Sea S F Western Mediterranean"
                             " - Gulf of Lyon",
                             "F Western Mediterranean M Gulf of Lyon")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "France"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "France"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('gulf-of-lyon', 'italy', 'western-mediterranean', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('gulf-of-lyon', 'turkey', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('marseilles', 'france', 'A')
                for u in units))

    def test_failing_hold_support_can_be_supported(self):
        # DATC 6.D.25
        units = {"Germany": ("A Berlin", "F Kiel"),
                 "Russia": ("F Baltic Sea", "A Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin S A Prussia",
                              "F Kiel S A Berlin"),
                  "Russia": ("F Baltic Sea S A Prussia - Berlin",
                             "A Prussia M Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('berlin', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'russia', 'A')
                for u in units))

    def test_failing_move_support_can_be_supported(self):
        # DATC 6.D.26
        units = {"Germany": ("A Berlin", "F Kiel"),
                 "Russia": ("F Baltic Sea", "A Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin S A Prussia - Silesia",
                              "F Kiel S A Berlin"),
                  "Russia": ("F Baltic Sea S A Prussia - Berlin",
                             "A Prussia M Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('berlin', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'russia', 'A')
                for u in units))

    def test_failing_convoy_can_be_supported(self):
        # DATC 6.D.27
        units = {"England": ("F Sweden", "F Denmark"),
                 "Germany": ("A Berlin",),
                 "Russia": ("F Baltic Sea", "F Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Sweden M Baltic Sea",
                              "F Denmark S F Sweden - Baltic Sea"),
                  "Germany": ("A Berlin H",),
                  "Russia": ("F Baltic Sea C A Berlin - Livonia",
                             "F Prussia S F Baltic Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('baltic-sea', 'russia', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('sweden', 'england', 'F')
                for u in units))

    def test_impossible_move_and_support(self):
        # DATC 6.D.28
        units = {"Austria": ("A Budapest",),
                 "Russia": ("F Rumania",),
                 "Turkey": ("F Black Sea", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Budapest S F Rumania",),
                  "Russia": ("F Rumania M Holland",),
                  "Turkey": ("F Black Sea M Rumania",
                             "A Bulgaria S F Black Sea - Rumania")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('rumania', 'russia', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('black-sea', 'turkey', 'F')
                for u in units))

    def test_move_to_impossible_coast_and_support(self):
        # DATC 6.D.29
        units = {"Austria": ("A Budapest",),
                 "Russia": ("F Rumania",),
                 "Turkey": ("F Black Sea", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Budapest S F Rumania",),
                  "Russia": ("F Rumania M Bulgaria (SC)",),
                  "Turkey": ("F Black Sea M Rumania",
                             "A Bulgaria S F Black Sea - Rumania")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('rumania', 'russia', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('black-sea', 'turkey', 'F')
                for u in units))

    def test_move_without_coast_and_support(self):
        # DATC 6.D.30
        units = {"Italy": ("F Aegean Sea",),
                 "Russia": ("F Constantinople",),
                 "Turkey": ("F Black Sea", "A Bulgaria")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("F Aegean Sea S F Constantinople",),
                  "Russia": ("F Constantinople M Bulgaria",),
                  "Turkey": ("F Black Sea M Constantinople",
                             "A Bulgaria S F Black Sea - Constantinople")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('constantinople', 'russia', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('black-sea', 'turkey', 'F')
                for u in units))

    def test_fleet_cant_support_and_convoy_simultaneously(self):
        # DATC 6.D.31
        # note: added 2nd order for F Black Sea, per the suggestion.
        units = {"Austria": ("A Rumania",),
                 "Turkey": ("F Black Sea",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Rumania M Armenia",),
                  "Turkey": ("F Black Sea S A Rumania - Armenia",)}
        create_orders(orders, T)
        orders = {"Turkey": ("F Black Sea M Constantinople",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        o = models.Order.objects.get(post__government__power__name="Turkey",
                                     action='S')
        self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        o = models.Order.objects.get(post__government__power__name="Turkey",
                                     action='M')
        self.assertTrue(is_legal(o.as_data(), units, owns, T.season))
        o = models.Order.objects.get(post__government__power__name=
                                     "Austria-Hungary")
        self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('rumania', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('constantinople', 'turkey', 'F')
                for u in units))

    def test_missing_fleet_convoy(self):
        # DATC 6.D.32
        units = {"England": ("F Edinburgh", "A Liverpool"),
                 "France": ("F London",),
                 "Germany": ("A Yorkshire",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Edinburgh S A Liverpool - Yorkshire",
                              "A Liverpool M Yorkshire"),
                  "France": ("F London S A Yorkshire",),
                  "Germany": ("A Yorkshire M Holland",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Germany"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Germany"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'])
                == ('yorkshire', 'germany', False)
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('liverpool', 'england', 'A')
                for u in units))

    def test_unwanted_support_allowed(self):
        # DATC 6.D.33
        units = {"Austria": ("A Serbia", "A Vienna"),
                 "Russia": ("A Galicia",),
                 "Turkey": ("A Bulgaria",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Serbia M Budapest",
                              "A Vienna M Budapest"),
                  "Russia": ("A Galicia S A Serbia - Budapest",),
                  "Turkey": ("A Bulgaria M Serbia",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('budapest', 'serbia', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('vienna', 'austria-hungary', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('serbia', 'turkey', 'A')
                for u in units))

    def test_support_targeting_own_area_not_allowed(self):
        # DATC 6.D.34
        units = {"Germany": ("A Berlin", "A Silesia", "F Baltic Sea"),
                 "Italy": ("A Prussia",),
                 "Russia": ("A Warsaw", "A Livonia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Prussia",
                              "A Silesia S A Berlin - Prussia",
                              "F Baltic Sea S A Berlin - Prussia"),
                  "Italy": ("A Prussia S A Livonia - Prussia",),
                  "Russia": ("A Warsaw S A Livonia - Prussia",
                             "A Livonia M Prussia")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Italy"):
            self.assertFalse(is_legal(o.as_data(), units, owns, T.season))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Italy"):
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'])
                == ('prussia', 'italy', 'berlin')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'germany', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('livonia', 'russia', 'A')
                for u in units))


class HeadToHeadAndBeleagueredGarrison(TestCase):
    """
    Based on section 6.E from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.E

    """
    def setUp(self):
        self.game = factories.GameFactory()
        self.turn = self.game.create_turn({'number': 0, 'year': 1900, 'season': 'S'})
        self.governments = [
            factories.GovernmentFactory(game=self.game, power=p)
            for p in standard.powers
        ]

    def test_dislodged_unit_has_no_effect_on_attackers_area(self):
        # DATC 6.E.1
        units = {"Germany": ("A Berlin", "F Kiel", "A Silesia"),
                 "Russia": ("A Prussia",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Prussia",
                              "F Kiel M Berlin",
                              "A Silesia S A Berlin - Prussia"),
                  "Russia": ("A Prussia M Berlin",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('berlin', 'kiel', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('prussia', 'berlin', 'germany', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('prussia', 'russia', 'berlin', 'A')
                for u in units))

    def test_no_self_dislodgement_in_head_to_head_battle(self):
        # DATC 6.E.2
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Kiel",
                              "F Kiel M Berlin",
                              "A Munich S A Berlin - Kiel")}
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
                == ('berlin', 'germany', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('kiel', 'germany', False, 'F')
                for u in units))

    def test_no_help_dislodging_own_unit(self):
        # DATC 6.E.3
        units = {"Germany": ("A Berlin", "A Munich"),
                 "England": ("F Kiel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Kiel",
                              "A Munich S F Kiel - Berlin"),
                  "England": ("F Kiel M Berlin",)}
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
                == ('kiel', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('berlin', 'germany', False, 'A')
                for u in units))

    def test_non_dislodged_loser_still_has_effect(self):
        # DATC 6.E.4
        units = {"Germany": ("F Holland", "F Helgoland Bight", "F Skagerrak"),
                 "France": ("F North Sea", "F Belgium"),
                 "England": ("F Edinburgh", "F Yorkshire", "F Norwegian Sea"),
                 "Austria": ("A Kiel", "A Ruhr")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Holland M North Sea",
                              "F Helgoland Bight S F Holland - North Sea",
                              "F Skagerrak S F Holland - North Sea"),
                  "France": ("F North Sea M Holland",
                             "F Belgium S F North Sea - Holland"),
                  "England": ("F Edinburgh S F Norwegian Sea - North Sea",
                              "F Yorkshire S F Norwegian Sea - North Sea",
                              "F Norwegian Sea M North Sea"),
                  "Austria": ("A Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('holland', 'germany', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norwegian-sea', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ruhr', 'austria-hungary', 'A')
                for u in units))

    def test_loser_dislodged_by_another_army_still_has_effect(self):
        # DATC 6.E.5
        units = {"Germany": ("F Holland", "F Helgoland Bight", "F Skagerrak"),
                 "France": ("F North Sea", "F Belgium"),
                 "England": ("F Edinburgh", "F Yorkshire",
                             "F Norwegian Sea", "F London"),
                 "Austria": ("A Kiel", "A Ruhr")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Holland M North Sea",
                              "F Helgoland Bight S F Holland - North Sea",
                              "F Skagerrak S F Holland - North Sea"),
                  "France": ("F North Sea M Holland",
                             "F Belgium S F North Sea - Holland"),
                  "England": ("F Edinburgh S F Norwegian Sea - North Sea",
                              "F Yorkshire S F Norwegian Sea - North Sea",
                              "F Norwegian Sea M North Sea",
                              "F London S F Norwegian Sea - North Sea"),
                  "Austria": ("A Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('holland', 'germany', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['displaced_from'], u['u_type'])
                == ('north-sea', 'france', 'norwegian-sea', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('north-sea', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ruhr', 'austria-hungary', 'A')
                for u in units))

    def test_not_dislodged_because_own_support_still_has_effect(self):
        # DATC 6.E.6
        units = {"Germany": ("F Holland", "F Helgoland Bight"),
                 "France": ("F North Sea", "F Belgium", "F English Channel"),
                 "Austria": ("A Kiel", "A Ruhr")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Holland M North Sea",
                              "F Helgoland Bight S F Holland - North Sea"),
                  "France": ("F North Sea M Holland",
                             "F Belgium S F North Sea - Holland",
                             "F English Channel S F Holland - North Sea"),
                  "Austria": ("A Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('holland', 'germany', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'france', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ruhr', 'austria-hungary', 'A')
                for u in units))

    def test_no_self_dislodgement_with_beleaguered_garrison(self):
        # DATC 6.E.7
        units = {"England": ("F North Sea", "F Yorkshire"),
                 "Germany": ("F Holland", "F Helgoland Bight"),
                 "Russia": ("F Skagerrak", "F Norway")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea H",
                              "F Yorkshire S F Norway - North Sea"),
                  "Germany": ("F Holland S F Helgoland Bight - North Sea",
                              "F Helgoland Bight M North Sea"),
                  "Russia": ("F Skagerrak S F Norway - North Sea",
                             "F Norway M North Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('helgoland-bight', 'germany', 'F')
                for u in units))

    def test_no_self_dislodgement_with_beleaguered_and_head_to_head(self):
        # DATC 6.E.8
        units = {"England": ("F North Sea", "F Yorkshire"),
                 "Germany": ("F Holland", "F Helgoland Bight"),
                 "Russia": ("F Skagerrak", "F Norway")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea M Norway",
                              "F Yorkshire S F Norway - North Sea"),
                  "Germany": ("F Holland S F Helgoland Bight - North Sea",
                              "F Helgoland Bight M North Sea"),
                  "Russia": ("F Skagerrak S F Norway - North Sea",
                             "F Norway M North Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('norway', 'russia', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('helgoland-bight', 'germany', 'F')
                for u in units))

    def test_almost_self_dislodgement_with_beleaguered_garrison(self):
        # DATC 6.E.9
        units = {"England": ("F North Sea", "F Yorkshire"),
                 "Germany": ("F Holland", "F Helgoland Bight"),
                 "Russia": ("F Skagerrak", "F Norway")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea M Norwegian Sea",
                              "F Yorkshire S F Norway - North Sea"),
                  "Germany": ("F Holland S F Helgoland Bight - North Sea",
                              "F Helgoland Bight M North Sea"),
                  "Russia": ("F Skagerrak S F Norway - North Sea",
                             "F Norway M North Sea")}
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
                == ('norwegian-sea', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('north-sea', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('helgoland-bight', 'germany', 'F')
                for u in units))

    def test_almost_circular_move_self_dislodgement_beleaguered_garrison(self):
        # DATC 6.E.10
        units = {"England": ("F North Sea", "F Yorkshire"),
                 "Germany": ("F Holland", "F Helgoland Bight", "F Denmark"),
                 "Russia": ("F Skagerrak", "F Norway")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea M Denmark",
                              "F Yorkshire S F Norway - North Sea"),
                  "Germany": ("F Holland S F Helgoland Bight - North Sea",
                              "F Helgoland Bight M North Sea",
                              "F Denmark M Helgoland Bight"),
                  "Russia": ("F Skagerrak S F Norway - North Sea",
                             "F Norway M North Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'england', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norway', 'russia', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('helgoland-bight', 'germany', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('denmark', 'germany', 'F')
                for u in units))

    def test_no_self_dislodgement_garrison_unit_swap(self):
        # DATC 6.E.11
        units = {"France": ("A Spain", "F Mid-Atlantic Ocean",
                            "F Gulf of Lyon"),
                 "Germany": ("A Marseilles", "A Gascony"),
                 "Italy": ("F Portugal", "F Western Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Spain M Portugal *", # * = via Convoy
                             "F Mid-Atlantic Ocean C A Spain - Portugal",
                             "F Gulf of Lyon S F Portugal - Spain (NC)"),
                  "Germany": ("A Marseilles S A Gascony - Spain",
                              "A Gascony M Spain"),
                  "Italy":
                      ("F Portugal M Spain (NC)",
                       "F Western Mediterranean S F Portugal - Spain (NC)")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), get_territory(u['previous']), u['government'], u['u_type'])
                == ('portugal', 'spain', 'france', 'A')
                for u in units))

        self.assertTrue(
            any((u['subregion'], u['government'], u['u_type'])
                == ('spain.nc.s', 'italy', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('gascony', 'germany', 'A')
                for u in units))

    def test_support_attack_on_own_unit_can_be_used_for_other_means(self):
        # DATC 6.E.12
        units = {"Austria": ("A Budapest", "A Serbia"),
                 "Italy": ("A Vienna",),
                 "Russia": ("A Galicia", "A Rumania")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Budapest M Rumania",
                              "A Serbia S A Vienna - Budapest"),
                  "Italy": ("A Vienna M Budapest",),
                  "Russia": ("A Galicia M Budapest",
                             "A Rumania S A Galicia - Budapest")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('budapest', 'austria-hungary', False, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('vienna', 'italy', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('galicia', 'russia', 'A')
                for u in units))

    def test_three_way_beleaguered_garrison(self):
        # DATC 6.E.13
        units = {"England": ("F Edinburgh", "F Yorkshire"),
                 "France": ("F Belgium", "F English Channel"),
                 "Germany": ("F North Sea",),
                 "Russia": ("F Norwegian Sea", "F Norway")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Edinburgh S F Yorkshire - North Sea",
                              "F Yorkshire M North Sea"),
                  "France": ("F Belgium M North Sea",
                             "F English Channel S F Belgium - North Sea"),
                  "Germany": ("F North Sea H",),
                  "Russia": ("F Norwegian Sea M North Sea",
                             "F Norway S F Norwegian Sea - North Sea")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('north-sea', 'germany', False, 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('yorkshire', 'england', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('belgium', 'france', 'F')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('norwegian-sea', 'russia', 'F')
                for u in units))

    def test_illegal_head_to_head_battle_can_still_defend(self):
        # DATC 6.E.14
        units = {"England": ("A Liverpool",),
                 "Russia": ("F Edinburgh",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh",),
                  "Russia": ("F Edinburgh M Liverpool",)}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        self.assertTrue(
            is_legal(
                models.Order.objects.get(post__government__power__name="England").as_data(),
                units, owns, T.season))
        self.assertFalse(
            is_legal(
                models.Order.objects.get(post__government__power__name="Russia").as_data(),
                units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('liverpool', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('edinburgh', 'russia', False, 'F')
                for u in units))

    def test_friendly_head_to_head_battle(self):
        # DATC 6.E.15
        units = {"England": ("F Holland", "A Ruhr"),
                 "France": ("A Kiel", "A Munich", "A Silesia"),
                 "Germany": ("A Berlin", "F Denmark", "F Helgoland Bight"),
                 "Russia": ("F Baltic Sea", "A Prussia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Holland S A Ruhr - Kiel",
                              "A Ruhr M Kiel"),
                  "France": ("A Kiel M Berlin",
                             "A Munich S A Kiel - Berlin",
                             "A Silesia S A Kiel - Berlin"),
                  "Germany": ("A Berlin M Kiel",
                              "F Denmark S A Berlin - Kiel",
                              "F Helgoland Bight S A Berlin - Kiel"),
                  "Russia": ("F Baltic Sea S A Prussia - Berlin",
                             "A Prussia M Berlin")}
        create_orders(orders, T)

        units = T.get_units()
        owns = T.get_ownership()
        for o in models.Order.objects.all():
            self.assertTrue(is_legal(o.as_data(), units, owns, T.season))

        T.game.generate()
        T = T.game.current_turn()
        units = T.get_units()

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('kiel', 'france', False, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['dislodged'], u['u_type'])
                == ('berlin', 'germany', False, 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('ruhr', 'england', 'A')
                for u in units))

        self.assertTrue(
            any((get_territory(u['subregion']), u['government'], u['u_type'])
                == ('prussia', 'russia', 'A')
                for u in units))
