from django.db.models import Count
from django.test import TestCase
from django.utils.unittest import expectedFailure

from .helpers import create_units, create_orders
from .. import models


class Retreating(TestCase):
    """
    Based on section 6.H from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.H

    """

    fixtures = ['basic_game.json']

    def test_no_supports_during_retreat(self):
        # DATC 6.H.1
        units = {"Austria": ("F Trieste", "A Serbia"),
                 "Turkey": ("F Greece",),
                 "Italy": ("A Venice", "A Tyrolia",
                           "F Ionian Sea", "F Aegean Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("F Trieste H",
                              "A Serbia H"),
                  "Turkey": ("F Greece H",),
                  "Italy": ("A Venice S A Tyrolia - Trieste",
                            "A Tyrolia M Trieste",
                            "F Ionian Sea M Greece",
                            "F Aegean Sea S F Ionian Sea - Greece")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"Austria": ("F Trieste M Albania",
                              "A Serbia S F Trieste - Albania"),
                  "Turkey": ("F Greece M Albania",)}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T, action='M'):
            self.assertTrue(T.is_legal(o))
        self.assertFalse(
            T.is_legal(models.Order.objects.get(post__turn=T, action='S')))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        austria = T.unit_set.filter(government__power__name="Austria-Hungary")
        self.assertEqual(austria.count(), 1)
        self.assertTrue(austria.filter(subregion__territory__name="Serbia",
                                       u_type='A').exists())

        turkey = T.unit_set.filter(government__power__name="Turkey")
        self.assertEqual(turkey.count(), 0)

    def test_no_supports_from_retreating_unit(self):
        # DATC 6.H.2
        units = {"England": ("A Liverpool", "F Yorkshire", "F Norway"),
                 "Germany": ("A Kiel", "A Ruhr"),
                 "Russia": ("F Edinburgh", "A Sweden",
                            "A Finland", "F Holland")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh",
                              "F Yorkshire S A Liverpool - Edinburgh",
                              "F Norway H"),
                  "Germany": ("A Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland"),
                  "Russia": ("F Edinburgh H",
                             "A Sweden S A Finland - Norway",
                             "A Finland M Norway",
                             "F Holland H")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"England": ("F Norway M North Sea",),
                  "Russia": ("F Edinburgh M North Sea",
                             "F Holland S F Edinburgh - North Sea")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T, action='M'):
            self.assertTrue(T.is_legal(o))
        self.assertFalse(
            T.is_legal(models.Order.objects.get(post__turn=T, action='S')))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 2)

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="England",
                previous__subregion__territory__name="Norway").exists())

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 2)

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Edinburgh").exists())

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Holland").exists())

    def test_no_convoy_during_retreat(self):
        # DATC 6.H.3
        units = {"England": ("F North Sea", "A Holland"),
                 "Germany": ("F Kiel", "A Ruhr")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea H",
                              "A Holland H"),
                  "Germany": ("F Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"England": ("A Holland M Yorkshire",
                              "F North Sea C A Holland - Yorkshire")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertFalse(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 1)

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="England",
                previous__subregion__territory__name="Holland").exists())

    def test_no_other_moves_during_retreat(self):
        # DATC 6.H.4
        units = {"England": ("F North Sea", "A Holland"),
                 "Germany": ("F Kiel", "A Ruhr")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea H",
                              "A Holland H"),
                  "Germany": ("F Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"England": ("A Holland M Belgium",
                              "F North Sea M Norwegian Sea")}
        create_orders(orders, T)

        o = models.Order.objects.get(
            post__turn=T, actor__territory__name="Holland")
        self.assertTrue(T.is_legal(o))
        o = models.Order.objects.get(
            post__turn=T, actor__territory__name="North Sea")
        self.assertFalse(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertTrue(
            T.unit_set.filter(
                government__power__name="England",
                subregion__territory__name="Belgium",
                previous__subregion__territory__name="Holland").exists())

        self.assertTrue(
            T.unit_set.filter(
                government__power__name="England",
                subregion__territory__name="North Sea").exists())

    def test_unit_may_not_retreat_to_area_it_was_attacked_from(self):
        # DATC 6.H.5
        units = {"Russia": ("F Constantinople", "F Black Sea"),
                 "Turkey": ("F Ankara",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Constantinople S F Black Sea - Ankara",
                             "F Black Sea M Ankara"),
                  "Turkey": ("F Ankara H",)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"Turkey": ("F Ankara M Black Sea",)}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertFalse(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertFalse(
            T.unit_set.filter(government__power__name="Turkey").exists())

    def test_unit_may_not_retreat_to_contested_area(self):
        # DATC 6.H.6
        units = {"Austria": ("A Budapest", "A Trieste"),
                 "Germany": ("A Munich", "A Silesia"),
                 "Italy": ("A Vienna",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Budapest S A Trieste - Vienna",
                              "A Trieste M Vienna"),
                  "Germany": ("A Munich M Bohemia",
                              "A Silesia M Bohemia"),
                  "Italy": ("A Vienna H",)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"Italy": ("A Vienna M Bohemia",)}
        create_orders(orders, T)

        self.assertFalse(
            T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.filter(government__power__name="Italy").exists())

    def test_two_retreats_to_same_area_disbands_units(self):
        # DATC 6.H.7
        units = {"Austria": ("A Budapest", "A Trieste"),
                 "Germany": ("A Munich", "A Silesia"),
                 "Italy": ("A Vienna", "A Bohemia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Budapest S A Trieste - Vienna",
                              "A Trieste M Vienna"),
                  "Germany": ("A Munich S A Silesia - Bohemia",
                              "A Silesia M Bohemia"),
                  "Italy": ("A Vienna H",
                            "A Bohemia H")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        orders = {"Italy": ("A Bohemia M Tyrolia",
                            "A Vienna M Tyrolia")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.filter(government__power__name="Italy").exists())

    def test_three_retreats_to_same_area_disbands_units(self):
        # DATC 6.H.8
        units = {"England": ("A Liverpool", "F Yorkshire", "F Norway"),
                 "Germany": ("A Kiel", "A Ruhr"),
                 "Russia": ("F Edinburgh", "A Sweden",
                            "A Finland", "F Holland")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh",
                              "F Yorkshire S A Liverpool - Edinburgh",
                              "F Norway H"),
                  "Germany": ("A Kiel S A Ruhr - Holland",
                              "A Ruhr M Holland"),
                  "Russia": ("F Edinburgh H",
                             "A Sweden S A Finland - Norway",
                             "A Finland M Norway",
                             "F Holland H")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 3)

        orders = {"England": ("F Norway M North Sea",),
                  "Russia": ("F Edinburgh M North Sea",
                             "F Holland M North Sea")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 2)

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="England",
                previous__subregion__territory__name="Norway").exists())

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 2)

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Edinburgh").exists())

        self.assertFalse(
            T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Holland").exists())

    def test_dislodged_unit_will_not_make_attackers_area_contested(self):
        # DATC 6.H.9
        units = {"England": ("F Helgoland Bight", "F Denmark"),
                 "Germany": ("A Berlin", "F Kiel", "A Silesia"),
                 "Russia": ("A Prussia",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Helgoland Bight M Kiel",
                              "F Denmark S F Helgoland Bight - Kiel"),
                  "Germany": ("A Berlin M Prussia",
                              "F Kiel H",
                              "A Silesia S A Berlin - Prussia"),
                  "Russia": ("A Prussia M Berlin",)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 2)

        orders = {"Germany": ("F Kiel M Berlin",)}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 3)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              previous__subregion__territory__name="Kiel",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_attackers_area_not_contested_for_other_retreats(self):
        # DATC 6.H.10
        units = {"England": ("A Kiel",),
                 "Germany": ("A Berlin", "A Munich", "A Prussia"),
                 "Russia": ("A Warsaw", "A Silesia")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Kiel H",),
                  "Germany": ("A Berlin M Kiel",
                              "A Munich S A Berlin - Kiel",
                              "A Prussia H"),
                  "Russia": ("A Warsaw M Prussia",
                             "A Silesia S A Warsaw - Prussia")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 2)

        orders = {"England": ("A Kiel M Berlin",),
                  "Germany": ("A Prussia M Berlin",)}
        create_orders(orders, T)

        self.assertFalse(
            T.is_legal(
                models.Order.objects.get(
                    post__turn=T,
                    post__government__power__name="England")))
        self.assertTrue(
            T.is_legal(
                models.Order.objects.get(
                    post__turn=T,
                    post__government__power__name="Germany")))
        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.filter(government__power__name="England").exists())

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 3)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              previous__subregion__territory__name="Prussia",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_retreat_when_dislodged_by_adjacent_convoy(self):
        # DATC 6.H.11
        units = {"France": ("A Gascony", "A Burgundy", "F Mid-Atlantic Ocean",
                            "F Western Mediterranean", "F Gulf of Lyon"),
                 "Italy": ("A Marseilles",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Gascony M Marseilles *", # via convoy
                             "A Burgundy S A Gascony - Marseilles",
                             "F Mid-Atlantic Ocean C A Gascony - Marseilles",
                             "F Western Mediterranean C A Gascony - Marseilles",
                             "F Gulf of Lyon C A Gascony - Marseilles"),
                  "Italy": ("A Marseilles H",)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Marseilles",
                              previous__subregion__territory__name="Gascony",
                              government__power__name="France",
                              u_type='A').exists())

        orders = {"Italy": ("A Marseilles M Gascony",)}
        create_orders(orders, T)

        self.assertTrue(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Italy").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gascony",
                              previous__subregion__territory__name="Marseilles",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_retreat_when_dislodged_by_adjacent_convoy_while_convoying(self):
        # DATC 6.H.12
        units = {"England": ("A Liverpool", "F Irish Sea",
                             "F English Channel", "F North Sea"),
                 "France": ("F Brest", "F Mid-Atlantic Ocean"),
                 "Russia": ("A Edinburgh", "F Norwegian Sea",
                            "F North Atlantic Ocean", "A Clyde")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh *", # via convoy
                              "F Irish Sea C A Liverpool - Edinburgh",
                              "F English Channel C A Liverpool - Edinburgh",
                              "F North Sea C A Liverpool - Edinburgh"),
                  "France":
                      ("F Brest M English Channel",
                       "F Mid-Atlantic Ocean S F Brest - English Channel"),
                  "Russia":
                      ("A Edinburgh M Liverpool *", # via convoy
                       "F Norwegian Sea C A Edinburgh - Liverpool",
                       "F North Atlantic Ocean C A Edinburgh - Liverpool",
                       "A Clyde S A Edinburgh - Liverpool")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 2)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              previous__subregion__territory__name="Edinburgh",
                              government__power__name="Russia",
                              u_type='A').exists())
        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='F').exists())

        orders = {"England": ("A Liverpool M Edinburgh",)}
        create_orders(orders, T)

        self.assertTrue(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate()
        T = T.game.current_turn()

        # We lose the fleet in the English Channel, since it didn't retreat.
        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 3)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              previous__subregion__territory__name="Liverpool",
                              government__power__name="England",
                              u_type='A').exists())

    def test_no_retreat_with_convoy_in_main_phase(self):
        # DATC 6.H.13
        units = {"England": ("A Picardy", "F English Channel"),
                 "France": ("A Paris", "A Brest")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Picardy H",
                              "F English Channel C A Picardy - London"),
                  "France": ("A Paris M Picardy",
                             "A Brest S A Paris - Picardy")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Picardy",
                              previous__subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

        orders = {"England": ("A Picardy M London",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 1)

    def test_no_retreat_with_support_in_main_phase(self):
        # DATC 6.H.14
        units = {"England": ("A Picardy", "F English Channel"),
                 "France": ("A Paris", "A Brest", "A Burgundy"),
                 "Germany": ("A Munich", "A Marseilles")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Picardy H",
                              "F English Channel S A Picardy - Belgium"),
                  "France": ("A Paris M Picardy",
                             "A Brest S A Paris - Picardy",
                             "A Burgundy H"),
                  "Germany": ("A Munich S A Marseilles - Burgundy",
                              "A Marseilles M Burgundy")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 2)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Picardy",
                              previous__subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Burgundy",
                              previous__subregion__territory__name="Marseilles",
                              government__power__name="Germany",
                              u_type='A').exists())

        orders = {"England": ("A Picardy M Belgium",),
                  "France": ("A Burgundy M Belgium",)}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="England").count(), 1)

        self.assertEqual(
            T.unit_set.filter(government__power__name="France").count(), 2)

    def test_no_coastal_crawl_in_retreat(self):
        # DATC 6.H.15
        units = {"England": ("F Portugal",),
                 "France": ("F Spain (SC)", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Portugal H",),
                  "France": ("F Spain (SC) M Portugal",
                             "F Mid-Atlantic Ocean S F Spain (SC) - Portugal")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Portugal",
                              previous__subregion__territory__name="Spain",
                              government__power__name="France",
                              u_type='F').exists())

        orders = {"England": ("F Portugal M Spain (NC)",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        orders = {"England": ("F Portugal M Mid-Atlantic Ocean",)}
        create_orders(orders, T)

        self.assertFalse(
            T.is_legal(
                models.Order.objects.get(
                    post__turn=T,
                    target__territory__name="Mid-Atlantic Ocean"))
        )

        orders = {"England": ("F Portugal M Spain (SC)",)}
        create_orders(orders, T)

        self.assertFalse(
            T.is_legal(
                models.Order.objects.get(
                    post__turn=T, target__territory__name="Spain",
                    target__subname="SC"))
        )

    def test_contested_for_both_coasts(self):
        # DATC 6.H.16
        units = {"France": ("F Mid-Atlantic Ocean", "F Gascony",
                            "F Western Mediterranean"),
                 "Italy": ("F Tunisia", "F Tyrrhenian Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Mid-Atlantic Ocean M Spain (NC)",
                             "F Gascony M Spain (NC)",
                             "F Western Mediterranean H"),
                  "Italy":
                      ("F Tunisia S F Tyrrhenian Sea - Western Mediterranean",
                       "F Tyrrhenian Sea M Western Mediterranean")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(dislodged=True).count(), 1)

        self.assertTrue(
            T.unit_set.filter(
                subregion__territory__name="Western Mediterranean",
                previous__subregion__territory__name="Tyrrhenian Sea",
                government__power__name="Italy", u_type='F').exists())

        orders = {"France": ("F Western Mediterranean M Spain (SC)",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="France").count(), 2)


class Building(TestCase):
    """
    Based on section 6.I from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.I

    """

    fixtures = ['adjustment_turn.json']

    def test_too_many_build_orders(self):
        # DATC 6.I.1
        units = {"Germany": ("F North Sea", "F English Channel")}
        T = models.Turn.objects.get()
        create_units(units, T)

        self.assertEqual(T.unit_set.count(), 2)
        gvt = models.Government.objects.get(power__name="Germany")
        self.assertEqual(gvt.builds_available(T), 1)

        orders = {"Germany": ("A Warsaw B",
                              "A Kiel B",
                              "A Munich B")}
        create_orders(orders, T)

        self.assertEqual(models.Order.objects.filter(post__turn=T).count(), 3)

        for o in models.Order.objects.filter(post__turn=T,
                                             actor__territory__name="Warsaw"):
            self.assertFalse(T.is_legal(o))

        for o in models.Order.objects.filter(
                post__turn=T).exclude(actor__territory__name="Warsaw"):
            self.assertTrue(T.is_legal(o))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 3)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_fleets_cannot_be_built_in_land_areas(self):
        # DATC 6.I.2

        # Note: this test does nothing useful, since the appearance of
        # unit type to the user is merely a proxy for Subregion type.
        # This situation can never occur, since there exists no sea
        # Subregion in Moscow's Territory.
        units = {"Russia": ("F St. Petersburg (SC)", "A Warsaw",
                            "F Sevastopol")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F Moscow B",)}
        create_orders(orders, T)

        self.assertTrue(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 3)

        self.assertFalse(
            T.unit_set.filter(subregion__territory__name="Moscow",
                              government__power__name="Russia").exists())

    def test_supply_center_must_be_empty_for_building(self):
        # DATC 6.I.3
        units = {"Germany": ("A Berlin", "F English Channel")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("A Berlin B",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 2)

    def test_both_coasts_must_be_empty_for_building(self):
        # DATC 6.I.4
        units = {"Russia": ("F St. Petersburg (SC)",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("F St. Petersburg (NC) B",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="St. Petersburg",
                              government__power__name="Russia",
                              subregion__subname="SC").exists())

    def test_building_in_home_supply_center_that_is_not_owned(self):
        # DATC 6.I.5
        T = models.Turn.objects.get()
        russia = models.Government.objects.get(power__name="Russia")
        T.ownership_set.filter(
            territory__name="Berlin").update(government=russia)

        orders = {"Germany": ("A Berlin B",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 0)

    def test_building_in_owned_supply_center_that_is_not_a_home_center(self):
        # DATC 6.I.6
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(
            territory__name="Warsaw").update(government=germany)

        orders = {"Germany": ("A Warsaw B",)}
        create_orders(orders, T)

        self.assertFalse(T.is_legal(models.Order.objects.get(post__turn=T)))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Germany").count(), 0)

    def test_only_one_build_in_a_home_supply_center(self):
        # DATC 6.I.7
        T = models.Turn.objects.get()

        orders = {"Russia": ("A Moscow B",
                             "A Moscow B")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)


class CivilDisorderAndDisbands(TestCase):
    """
    Based on section 6.J from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.J

    """

    fixtures = ['adjustment_turn.json']

    def test_too_many_remove_orders(self):
        # DATC 6.J.1
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="France").exclude(
            territory__name="Marseilles").update(government=germany)

        units = {"France": ("A Paris", "A Picardy")}
        create_units(units, T)

        orders = {"France": ("F Gulf of Lyon D",
                             "A Picardy D",
                             "A Paris D")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(
                post__turn=T).exclude(actor__territory__name="Gulf of Lyon"):
            self.assertTrue(T.is_legal(o))

        for o in models.Order.objects.filter(
                post__turn=T, actor__territory__name="Gulf of Lyon"):
            self.assertFalse(T.is_legal(o))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="France").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

    def test_removing_the_same_unit_twice(self):
        # DATC 6.J.2
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="France").exclude(
            territory__name="Marseilles").update(government=germany)

        units = {"France": ("A Paris", "F English Channel", "F North Sea")}
        create_units(units, T)

        orders = {"France": ("A Paris D",
                             "A Paris D")}
        create_orders(orders, T)

        for o in models.Order.objects.filter(post__turn=T):
            self.assertTrue(T.is_legal(o))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="France").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              u_type='F').exists())

    def test_civil_disorder_two_armies_with_different_distance(self):
        # DATC 6.J.3
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("A Livonia", "A Sweden")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Livonia",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_civil_disorder_two_armies_with_equal_distance(self):
        # DATC 6.J.4
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("A Livonia", "A Ukraine")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ukraine",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_civil_disorder_two_fleets_with_different_distance(self):
        # DATC 6.J.5
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("F Skagerrak", "F Berlin")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_civil_disorder_two_fleets_with_equal_distance(self):
        # DATC 6.J.6
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("F Berlin", "F Helgoland Bight")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_civil_disorder_two_fleets_and_army_with_equal_distance(self):
        # DATC 6.J.7
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").exclude(
            territory__name="Warsaw").update(government=germany)

        units = {"Russia": ("A Bohemia", "F Skagerrak", "F North Sea")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 2)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bohemia",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_civil_disorder_fleet_with_shorter_distance_than_army(self):
        # DATC 6.J.8
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("A Tyrolia", "F Baltic Sea")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_civil_disorder_must_be_counted_from_both_coasts(self):
        # DATC 6.J.9
        T = models.Turn.objects.get()
        germany = models.Government.objects.get(power__name="Germany")
        T.ownership_set.filter(government__power__name="Russia").exclude(
            territory__name="Moscow").update(government=germany)

        units = {"Russia": ("A Tyrolia", "F Skagerrak")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Russia").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_civil_disorder_counting_convoying_distance(self):
        # DATC 6.J.10
        T = models.Turn.objects.get()
        france = models.Government.objects.get(power__name="France")
        T.ownership_set.filter(government__power__name="Italy").exclude(
            territory__name="Rome").exclude(
            territory__name="Venice").update(government=france)

        units = {"Italy": ("F Ionian Sea", "A Greece", "A Silesia")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Italy").count(), 2)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              government__power__name="Italy",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_civil_disorder_counting_distance_without_convoying_fleet(self):
        # DATC 6.J.11
        T = models.Turn.objects.get()
        france = models.Government.objects.get(power__name="France")
        T.ownership_set.filter(government__power__name="Italy").exclude(
            territory__name="Rome").update(government=france)

        units = {"Italy": ("A Greece", "A Silesia")}
        create_units(units, T)

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertEqual(
            T.unit_set.filter(government__power__name="Italy").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Italy",
                              u_type='A').exists())
