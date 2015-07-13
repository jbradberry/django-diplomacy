from .. import models
from .helpers import create_units, create_orders
from django.test import TestCase


class SupportsAndDislodges(TestCase):
    """
    Based on section 6.D from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.D

    """

    fixtures = ['basic_game.json']

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary"
                              ).exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              dislodged=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Austria-Hungary"
                              ).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna",
                              government__power__name="Austria-Hungary"
                              ).exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              government__power__name="Italy"
                              ).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              ).exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

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
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Livonia",
                              government__power__name="Russia",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Germany",
                              dislodged=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Finland",
                              government__power__name="Russia").exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Turkey",
                              dislodged=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              dislodged=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_self_dislodgement_prohibited(self):
        # DATC 6.D.10
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin H",
                              "F Kiel M Berlin",
                              "A Munich S F Kiel - Berlin")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              dislodged=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              dislodged=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Warsaw",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Apulia",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              dislodged=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              previous__subregion__territory__name="Venice",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              dislodged=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Russia",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              dislodged=True,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="France",
                              u_type='A').exists())

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
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              previous__subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              displaced_from__name="Black Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              previous__subregion__territory__name="Black Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Armenia",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              previous__subregion__territory__name="Black Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              government__power__name="Turkey",
                              displaced_from__name="Black Sea",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__name="North Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name="North Sea",
                              government__power__name="England",
                              u_type='F').exists())

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
            T.unit_set.filter(subregion__territory__name="Munich",
                              previous__subregion__territory__name="Silesia",
                              government__power__name="Russia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice",
                              government__power__name="Italy",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              dislodged=False,
                              u_type='F').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Germany"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="Germany",
                              displaced_from__name="Munich",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              previous__subregion__territory__name="Munich",
                              government__power__name="Russia").exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "France"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.filter(post__government__power__name=
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
                              government__power__name="Italy").exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "France"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "France"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gulf of Lyon",
                              government__power__name="Italy",
                              displaced_from__name="Western Mediterranean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gulf of Lyon",
                              government__power__name="Turkey",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Marseilles",
                              government__power__name="France",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Russia",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='F').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rumania",
                              government__power__name="Russia",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rumania",
                              government__power__name="Russia",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

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

        o = models.Order.objects.get(post__government__power__name="Turkey",
                                     action='S')
        self.assertTrue(not T.is_legal(o))
        o = models.Order.objects.get(post__government__power__name="Turkey",
                                     action='M')
        self.assertTrue(T.is_legal(o))
        o = models.Order.objects.get(post__government__power__name=
                                     "Austria-Hungary")
        self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rumania",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Turkey",
                              u_type='F').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Germany"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Germany"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              government__power__name="Germany",
                              dislodged=False).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="England",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Budapest",
                              previous__subregion__territory__name="Serbia",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Serbia",
                              government__power__name="Turkey",
                              u_type='A').exists())

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

        for o in models.Order.objects.filter(post__government__power__name=
                                             "Italy"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(post__government__power__name=
                                              "Italy"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Italy",
                              displaced_from__name="Berlin").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Germany",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Livonia",
                              government__power__name="Russia",
                              u_type='A').exists())


class HeadToHeadAndBeleagueredGarrison(TestCase):
    """
    Based on section 6.E from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.E

    """

    fixtures = ['basic_game.json']

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              previous__subregion__territory__name="Kiel",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              previous__subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              displaced_from__name="Berlin",
                              u_type='A').exists())

    def test_no_self_dislodgement_in_head_to_head_battle(self):
        # DATC 6.E.2
        units = {"Germany": ("A Berlin", "F Kiel", "A Munich")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin M Kiel",
                              "F Kiel M Berlin",
                              "A Munich S A Berlin - Kiel")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norwegian Sea",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              displaced_from__name="Norwegian Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Germany",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Germany",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norwegian Sea",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Germany",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Denmark",
                              government__power__name="Germany",
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Portugal",
                              previous__subregion__territory__name="Spain",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              government__power__name="Italy",
                              subregion__subname="NC",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gascony",
                              government__power__name="Germany",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Budapest",
                              government__power__name="Austria-Hungary",
                              dislodged=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna",
                              government__power__name="Italy",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Galicia",
                              government__power__name="Russia",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norwegian Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_illegal_head_to_head_battle_can_still_defend(self):
        # DATC 6.E.14
        units = {"England": ("A Liverpool",),
                 "Russia": ("F Edinburgh",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh",),
                  "Russia": ("F Edinburgh M Liverpool",)}
        create_orders(orders, T)

        self.assertTrue(
            T.is_legal(
                models.Order.objects.get(post__government__power__name="England")))
        self.assertFalse(
            T.is_legal(
                models.Order.objects.get(post__government__power__name="Russia")))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              government__power__name="Russia",
                              dislodged=False,
                              u_type='F').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="France",
                              dislodged=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              dislodged=False,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())
