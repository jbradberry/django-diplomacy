import models, forms
from django.test import TestCase
from django.db.models import Count
from django.core.management import call_command
from django.contrib.auth.models import User

options = {'commit': False, 'verbosity': 0}
u_convert = dict((v, k) for k,v in models.convert.iteritems())

unit_subs = dict(("{0} {1}{2}".format(models.convert[s.sr_type],
                                      s.territory.name,
                                      ' {0}'.format(s.subname) if s.subname
                                      else ''),
                  s)
                  for s in models.Subregion.objects.select_related('territory'))
subs_unit = dict((v.id, k) for k,v in unit_subs.iteritems())
territory = dict((t.name, t.id) for t in models.Territory.objects.all())


def create_unit(turn, gvt, unit, **kwargs):
    sr = unit_subs[unit]
    for field, val in kwargs.iteritems():
        if val in territory:
            kwargs[field] = territory[val]
    return models.Unit.objects.create(u_type=models.convert[sr.sr_type],
                                      subregion=sr, turn=turn, government=gvt,
                                      **kwargs)

def create_units(units, turn):
    for gname, uset in units.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        for u_opts in uset:
            create_unit(turn, gvt, u_opts[0],
                        **({} if len(u_opts) == 1 else u_opts[1]))

def fetch(desc, match=None):
    if not desc:
        return None
    if match:
        srs = dict((u_type, "{0} {1}".format(u_type, desc))
                   for u_type in ('A', 'F'))
        u_type = models.convert[unit_subs[match].sr_type]
        if srs[u_type] not in unit_subs:
            # It won't produce a legal order, but this will give a
            # placeholder that isn't far removed from the intention.
            del srs[u_type]
            desc = srs.values()[0]
        else:
            desc = srs[u_type]
    return unit_subs[desc]

def create_order(turn, gvt, slot, actor, action, assist=None, target=None,
                 via_convoy=False):
    return models.Order.objects.create(
        turn=turn, government=gvt, slot=slot,
        actor=fetch(actor), action=action, assist=fetch(assist),
        target=fetch(target, assist if assist else actor),
        via_convoy=bool(via_convoy))

def create_orders(orders, turn):
    for gname, oset in orders.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        for o_opts in oset:
            create_order(turn, gvt, *o_opts)


class CorrectnessHelperTest(TestCase):
    fixtures = ['basic_game.json']

    def test_find_convoys(self):
        units = {'England': (('F Mid-Atlantic Ocean',),
                             ('F English Channel',),
                             ('F Western Mediterranean',),
                             ('F Spain NC',),     # coastal, can't participate
                             ('F Ionian Sea',),   # fake group
                             ('F Adriatic Sea',), # fake group
                             ('F Baltic Sea',),
                             ('F Gulf of Bothnia',),
                             ('A Gascony',),
                             ('A Sweden',))}
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
            set(n[0] for n in units['England'][:3]))

        self.assertEqual(len(lands1), 10)
        self.assertEqual(
            set(sr.territory.name for sr in full_sr.filter(id__in=lands1)),
            set(['Tunisia', 'North Africa', 'London', 'Wales', 'Spain',
                 'Brest', 'Gascony', 'Picardy', 'Belgium', 'Portugal']))

        self.assertEqual(len(seas2), 2)
        self.assertEqual(
            set(subs_unit[sr.id] for sr in full_sr.filter(id__in=seas2)),
            set(n[0] for n in units['England'][6:8]))

        self.assertEqual(len(lands2), 8)
        self.assertEqual(
            set(sr.territory.name for sr in full_sr.filter(id__in=lands2)),
            set(['Prussia', 'Berlin', 'Kiel', 'Denmark', 'Sweden',
                 'Finland', 'St. Petersburg', 'Livonia']))


class BasicChecks(TestCase):
    """
    Based on section 6.A from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.A

    """

    fixtures = ['basic_game.json']

    def test_non_adjacent_move(self):
        # DATC 6.A.1
        units = {"England": (("F North Sea",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ((0, "F North Sea", "M", None, "Picardy"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_army_to_sea(self):
        # DATC 6.A.2
        units = {"England": (("A Liverpool",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ((0, "A Liverpool", "M", None, "Irish Sea"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_fleet_to_land(self):
        # DATC 6.A.3
        units = {"Germany": (("F Kiel",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ((0, "F Kiel", "M", None, "Munich"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector(self):
        # DATC 6.A.4
        units = {"Germany": (("F Kiel",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ((0, "F Kiel", "M", None, "Kiel"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector_with_convoy(self):
        # DATC 6.A.5
        units = {"England": (("F North Sea",),
                             ("A Yorkshire",),
                             ("A Liverpool",)),
                 "Germany": (("F London",),
                             ("A Wales",))}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England":
                      ((0, "F North Sea", "C", "A Yorkshire", "Yorkshire"),
                       (1, "A Yorkshire", "M", None, "Yorkshire"),
                       (2, "A Liverpool", "S", "A Yorkshire", "Yorkshire")),
                  "Germany":
                      ((0, "F London", "M", None, "Yorkshire"),
                       (1, "A Wales", "S", "F London", "Yorkshire"))}
        create_orders(orders, T)

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
        units = {"England": (("F London",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ((0, "F London", "M", None, "North Sea"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_only_armies_can_be_convoyed(self):
        # DATC 6.A.7
        units = {"England": (("F London",),
                             ("F North Sea",))}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ((0, "F London", "M", None, "Belgium"),
                              (1, "F North Sea", "C", "F London", "Belgium"))}
        create_orders(orders, T)

        orders = models.Order.objects.all()

        self.assertTrue(not T.is_legal(orders.get(slot=0)))
        self.assertTrue(not T.is_legal(orders.get(slot=1)))

    def test_support_to_hold_yourself(self):
        # DATC 6.A.8
        units = {"Italy": (("A Venice",),
                           ("A Tyrolia",)),
                 "Austria": (("F Trieste",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ((0, "A Venice", "M", None, "Trieste"),
                            (1, "A Tyrolia", "S", "A Venice", "Trieste")),
                  "Austria": ((0, "F Trieste", "S", "F Trieste"),)}
        create_orders(orders, T)

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
        units = {"Italy": (("F Rome",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ((0, "F Rome", "M", None, "Venice"),)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_support_on_unreachable_destination(self):
        # DATC 6.A.10
        units = {"Austria": (("A Venice",),),
                 "Italy": (("F Rome",),
                           ("A Apulia",))}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ((0, "A Venice", "H"),),
                  "Italy": ((0, "F Rome", "S", "A Apulia", "Venice"),
                            (1, "A Apulia", "M", None, "Venice"))}
        create_orders(orders, T)

        order = models.Order.objects.get(
            actor__territory__name="Rome")

        self.assertTrue(not T.is_legal(order))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            not T.unit_set.filter(displaced_from__isnull=False).exists())

    def test_simple_bounce(self):
        # DATC 6.A.11
        units = {"Austria": (("A Vienna",),),
                 "Italy": (("A Venice",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ((0, "A Vienna", "M", None, "Tyrolia"),),
                  "Italy": ((0, "A Venice", "M", None, "Tyrolia"),)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna").exists())
        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Venice").exists())
        self.assertEqual(
            T.unit_set.filter(standoff_from__name="Tyrolia").count(), 2)

    def test_bounce_of_three_units(self):
        # DATC 6.A.12
        units = {"Austria": (("A Vienna",),),
                 "Germany": (("A Munich",),),
                 "Italy": (("A Venice",),)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ((0, "A Vienna", "M", None, "Tyrolia"),),
                  "Germany": ((0, "A Munich", "M", None, "Tyrolia"),),
                  "Italy": ((0, "A Venice", "M", None, "Tyrolia"),)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

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

    def test_failing_move_support_can_be_supported(self):
        # DATC 6.D.26
        call_command('loaddata', '6D26.json', **options)

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

    def test_failing_convoy_can_be_supported(self):
        # DATC 6.D.27
        call_command('loaddata', '6D27.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Baltic Sea",
                              government__power__name="Russia",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='F').exists())

    def test_impossible_move_and_support(self):
        # DATC 6.D.28
        call_command('loaddata', '6D28.json', **options)


        T = models.Turn.objects.get()
        for o in models.Order.objects.filter(government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rumania",
                              government__power__name="Russia",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

    def test_move_to_impossible_coast_and_support(self):
        # DATC 6.D.29
        call_command('loaddata', '6D29.json', **options)


        T = models.Turn.objects.get()
        for o in models.Order.objects.filter(government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rumania",
                              government__power__name="Russia",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Black Sea",
                              government__power__name="Turkey",
                              u_type='F').exists())

#     def test_move_without_coast_and_support(self):
#         # DATC 6.D.30
#         # parser test

    def test_fleet_cant_support_and_convoy_simultaneously(self):
        # DATC 6.D.31
        # note: added 2nd order for F Black Sea, per the suggestion.
        call_command('loaddata', '6D31.json', **options)

        T = models.Turn.objects.get()
        o = models.Order.objects.get(government__power__name="Turkey",
                                     action='S')
        self.assertTrue(not T.is_legal(o))
        o = models.Order.objects.get(government__power__name="Turkey",
                                     action='M')
        self.assertTrue(T.is_legal(o))
        o = models.Order.objects.get(government__power__name=
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
        call_command('loaddata', '6D32.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.filter(government__power__name=
                                             "Germany"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
                                              "Germany"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="England",
                              u_type='A').exists())

    def test_unwanted_support_allowed(self):
        # DATC 6.D.33
        call_command('loaddata', '6D33.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Budapest",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Serbia",
                              government__power__name="Turkey",
                              u_type='A').exists())

    def test_support_targeting_own_area_not_allowed(self):
        # DATC 6.D.34
        call_command('loaddata', '6D34.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.filter(government__power__name=
                                             "Italy"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
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


class HeadToHeadAndBeleagueredGarrison(TestCase):
    """
    Based on section 6.E from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.E

    """

    fixtures = ['basic_game.json']

    def test_dislodged_unit_has_no_effect_on_attackers_area(self):
        # DATC 6.E.1
        call_command('loaddata', '6E01.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              displaced_from__name="Berlin",
                              u_type='A').exists())

    def test_no_self_dislodgement_in_head_to_head_battle(self):
        # DATC 6.E.2
        call_command('loaddata', '6E02.json', **options)

        T = models.Turn.objects.get()
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
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_no_help_dislodging_own_unit(self):
        # DATC 6.E.3
        call_command('loaddata', '6E03.json', **options)

        T = models.Turn.objects.get()
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
                              displaced_from__isnull=True,
                              u_type='A').exists())

    def test_non_dislodged_loser_still_has_effect(self):
        # DATC 6.E.4
        call_command('loaddata', '6E04.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

    def test_loser_dislodged_by_another_army_still_has_effect(self):
        # DATC 6.E.5
        call_command('loaddata', '6E05.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              displaced_from__name="Norwegian Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              displaced_from__isnull=True).exists())

    def test_not_dislodged_because_own_support_still_has_effect(self):
        # DATC 6.E.6
        call_command('loaddata', '6E06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

    def test_no_self_dislodgement_with_beleaguered_garrison(self):
        # DATC 6.E.7
        call_command('loaddata', '6E07.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
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
        call_command('loaddata', '6E08.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Helgoland Bight",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_almost_self_dislodgement_with_beleaguered_garrison(self):
        # DATC 6.E.9
        call_command('loaddata', '6E09.json', **options)

        T = models.Turn.objects.get()
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
        call_command('loaddata', '6E10.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
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
        call_command('loaddata', '6E11.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Portugal",
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
        call_command('loaddata', '6E12.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Budapest",
                              government__power__name="Austria-Hungary",
                              displaced_from__isnull=True,
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
        call_command('loaddata', '6E13.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Germany",
                              displaced_from__isnull=True,
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
        call_command('loaddata', '6E14.json', **options)

        T = models.Turn.objects.get()
        self.assertTrue(T.is_legal(
                models.Order.objects.get(government__power__name="England")))
        self.assertTrue(not T.is_legal(
                models.Order.objects.get(government__power__name="Russia")))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_friendly_head_to_head_battle(self):
        # DATC 6.E.15
        call_command('loaddata', '6E15.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Kiel",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Berlin",
                              government__power__name="Germany",
                              displaced_from__isnull=True,
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ruhr",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Prussia",
                              government__power__name="Russia",
                              u_type='A').exists())


class Convoys(TestCase):
    """
    Based on section 6.F from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.F

    """

    fixtures = ['basic_game.json']

    def test_no_convoy_in_coastal_areas(self):
        # DATC 6.F.1
        call_command('loaddata', '6F01.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(not T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Greece",
                              government__power__name="Turkey",
                              u_type='A').exists())

    def test_convoyed_army_can_bounce(self):
        # DATC 6.F.2
        call_command('loaddata', '6F02.json', **options)

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
            T.unit_set.filter(subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

    def test_convoyed_army_can_receive_support(self):
        # DATC 6.F.3
        call_command('loaddata', '6F03.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

    def test_attacked_convoy_is_not_disrupted(self):
        # DATC 6.F.4
        call_command('loaddata', '6F04.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="England",
                              u_type='A').exists())

    def test_beleaguered_convoy_is_not_disrupted(self):
        # DATC 6.F.5
        call_command('loaddata', '6F05.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodged_convoy_does_not_cut_support(self):
        # DATC 6.F.6
        call_command('loaddata', '6F06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__name="Skagerrak",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_dislodged_convoy_does_not_cause_contested_area(self):
        # DATC 6.F.7
        call_command('loaddata', '6F07.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__name="Skagerrak",
                              u_type='F').exists())

        u = T.unit_set.get(subregion__territory__name="North Sea",
                           government__power__name="England",
                           displaced_from__name="Skagerrak",
                           u_type='F')

        order = {'government': u.government, 'turn': T,
                 'actor': u.subregion, 'action': 'M', 'assist': None,
                 'target': models.Subregion.objects.get(territory__name=
                                                        "Holland",
                                                        sr_type='S')}
        self.assertTrue(T.is_legal(order))

    def test_dislodged_convoy_does_not_cause_a_bounce(self):
        # DATC 6.F.8
        call_command('loaddata', '6F08.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__name="Skagerrak",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy(self):
        # DATC 6.F.9
        call_command('loaddata', '6F09.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="England",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy_with_foreign_fleet(self):
        # DATC 6.F.10
        call_command('loaddata', '6F10.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="Germany",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy_with_only_foreign_fleets(self):
        # DATC 6.F.11
        call_command('loaddata', '6F11.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="Germany",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodged_convoying_fleet_not_on_route(self):
        # DATC 6.F.12
        call_command('loaddata', '6F12.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Irish Sea",
                              government__power__name="England",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_the_unwanted_alternative(self):
        # DATC 6.F.13
        call_command('loaddata', '6F13.json', **options)

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
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__name="Denmark",
                              u_type='F').exists())

    def test_simple_convoy_paradox(self):
        # DATC 6.F.14
        call_command('loaddata', '6F14.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__name="Wales",
                              u_type='F').exists())

    def test_simple_convoy_paradox_with_additional_convoy(self):
        # DATC 6.F.15
        call_command('loaddata', '6F15.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__name="Wales",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Wales",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_pandins_paradox(self):
        # DATC 6.F.16
        call_command('loaddata', '6F16.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

    def test_pandins_extended_paradox(self):
        # DATC 6.F.17
        call_command('loaddata', '6F17.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

    def test_betrayal_paradox(self):
        # DATC 6.F.18
        call_command('loaddata', '6F18.json', **options)

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
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_multi_route_convoy_disruption_paradox(self):
        # DATC 6.F.19
        call_command('loaddata', '6F19.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Tyrrhenian Sea",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rome",
                              government__power__name="Italy",
                              u_type='F').exists())

    def test_unwanted_multi_route_convoy_paradox(self):
        # DATC 6.F.20
        call_command('loaddata', '6F20.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              government__power__name="Italy",
                              displaced_from__name="Eastern Mediterranean",
                              u_type='F').exists())

    def test_dads_army(self):
        # DATC 6.F.21
        call_command('loaddata', '6F21.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Atlantic Ocean",
                              government__power__name="England",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

    def test_second_order_paradox_with_two_solutions(self):
        # DATC 6.F.22
        call_command('loaddata', '6F22.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__name="Picardy",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__name="Edinburgh",
                              u_type='F').exists())

    def test_second_order_paradox_with_two_exclusive_convoys(self):
        # DATC 6.F.23
        call_command('loaddata', '6F23.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
                              u_type='F').exists())

    def test_second_order_paradox_with_no_resolution(self):
        # DATC 6.F.24
        call_command('loaddata', '6F24.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__name="Edinburgh",
                              u_type='F').exists())


class ConvoyingToAdjacent(TestCase):
    """
    Based on section 6.G from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.G

    """

    fixtures = ['basic_game.json']

    def test_two_units_can_swap_by_convoy(self):
        # DATC 6.G.1
        call_command('loaddata', '6G01.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_kidnapping_an_army(self):
        # DATC 6.G.2
        call_command('loaddata', '6G02.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Russia",
                              u_type='F').exists())

    def test_kidnapping_with_disrupted_convoy(self):
        # DATC 6.G.3
        call_command('loaddata', '6G03.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="England",
                              displaced_from__name="Brest",
                              u_type='F').exists())

    def test_kidnapping_with_disrupted_convoy_and_opposite_move(self):
        # DATC 6.G.4
        call_command('loaddata', '6G04.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="England",
                              displaced_from__name="Brest",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              displaced_from__name="Picardy",
                              u_type='A').exists())

    def test_swapping_with_intent(self):
        # DATC 6.G.5
        call_command('loaddata', '6G05.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Apulia",
                              government__power__name="Italy",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rome",
                              government__power__name="Turkey",
                              u_type='A').exists())

    def test_swapping_with_unintended_intent(self):
        # DATC 6.G.6
        call_command('loaddata', '6G06.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_swapping_with_illegal_intent(self):
        # DATC 6.G.7
        call_command('loaddata', '6G07.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.exclude(actor__territory__name=
                                              "Gulf of Bothnia"):
            self.assertTrue(T.is_legal(o))
        self.assertTrue(not T.is_legal(models.Order.objects.get(
                    actor__territory__name="Gulf of Bothnia")))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_explicit_convoy_that_isnt_there(self):
        # DATC 6.G.8
        call_command('loaddata', '6G08.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="France",
                              u_type='A').exists())

    def test_swapped_or_dislodged(self):
        # DATC 6.G.9
        call_command('loaddata', '6G09.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
                              u_type='A').exists())

    def test_swapped_or_head_to_head(self):
        # DATC 6.G.10
        call_command('loaddata', '6G10.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Russia",
                              displaced_from__name="Norway",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norwegian Sea",
                              government__power__name="France",
                              u_type='F').exists())

    def test_convoy_to_adjacent_place_with_paradox(self):
        # DATC 6.G.11
        call_command('loaddata', '6G11.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Russia",
                              displaced_from__name="North Sea",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_swapping_two_units_with_two_convoys(self):
        # DATC 6.G.12
        call_command('loaddata', '6G12.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Liverpool",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_support_cut_on_attack_on_itself_via_convoy(self):
        # DATC 6.G.13
        call_command('loaddata', '6G13.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              displaced_from__name="Albania",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Trieste",
                              government__power__name="Italy",
                              u_type='F').exists())

    def test_bounce_by_convoy_to_adjacent_place(self):
        # DATC 6.G.14
        call_command('loaddata', '6G14.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="Russia",
                              displaced_from__name="Norway",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norwegian Sea",
                              government__power__name="France",
                              u_type='F').exists())

    def test_bounce_and_dislodge_with_double_convoy(self):
        # DATC 6.G.15
        call_command('loaddata', '6G15.json', **options)

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
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="France",
                              displaced_from__name="London",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              government__power__name="England",
                              u_type='A').exists())

    def test_two_units_in_one_area_bug_by_convoy(self):
        # DATC 6.G.16
        call_command('loaddata', '6G16.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertEqual(
            T.unit_set.filter(subregion__territory__name="Norway").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              u_type='F').exists())

    def test_two_units_in_one_area_bug_moving_over_land(self):
        # DATC 6.G.17
        call_command('loaddata', '6G17.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Sweden",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertEqual(
            T.unit_set.filter(subregion__territory__name="Norway").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              u_type='F').exists())

    def test_two_units_in_one_area_bug_with_double_convoy(self):
        # DATC 6.G.18
        call_command('loaddata', '6G18.json', **options)

        T = models.Turn.objects.get()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertEqual(
            T.unit_set.filter(subregion__territory__name="London").count(), 1)

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Yorkshire",
                              government__power__name="England",
                              u_type='A').exists())


class Retreating(TestCase):
    """
    Based on section 6.H from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.H

    """

    fixtures = ['basic_game.json']

    def test_no_supports_during_retreat(self):
        # DATC 6.H.1
        call_command('loaddata', '6H01.json', **options)

        T = models.Turn.objects.latest()

        o1, o2, o3 = models.Order.objects.all()
        self.assertTrue(T.is_legal(o1))
        self.assertTrue(not T.is_legal(o2))
        self.assertTrue(T.is_legal(o3))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="Austria-Hungary",
                previous__subregion__territory__name="Trieste").exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="Turkey",
                previous__subregion__territory__name="Greece").exists())

    def test_no_supports_from_retreating_unit(self):
        # DATC 6.H.2
        call_command('loaddata', '6H02.json', **options)

        T = models.Turn.objects.latest()

        o1, o2, o3 = models.Order.objects.all()
        self.assertTrue(T.is_legal(o1))
        self.assertTrue(T.is_legal(o2))
        self.assertTrue(not T.is_legal(o3))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="England",
                previous__subregion__territory__name="Norway").exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Edinburgh").exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="Russia",
                previous__subregion__territory__name="Holland").exists())

    def test_no_convoy_during_retreat(self):
        # DATC 6.H.3
        call_command('loaddata', '6H03.json', **options)

        T = models.Turn.objects.latest()
        for o in models.Order.objects.all():
            self.assertTrue(not T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertTrue(
            not T.unit_set.filter(
                government__power__name="England",
                previous__subregion__territory__name="Holland").exists())

    def test_no_other_moves_during_retreat(self):
        # DATC 6.H.4
        call_command('loaddata', '6H04.json', **options)

        T = models.Turn.objects.latest()
        o1, o2 = models.Order.objects.all()
        self.assertTrue(T.is_legal(o1))
        self.assertTrue(not T.is_legal(o2))

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
        call_command('loaddata', '6H05.json', **options)

        T = models.Turn.objects.latest()
        for o in models.Order.objects.all():
            self.assertTrue(not T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertFalse(
            T.unit_set.values('subregion__territory'
                              ).annotate(count=Count('subregion__territory')
                                         ).filter(count__gt=1).exists())

        self.assertTrue(
            not T.unit_set.filter(government__power__name="Turkey").exists())

    def test_unit_may_not_retreat_to_contested_area(self):
        # DATC 6.H.6
        call_command('loaddata', '6H06.json', **options)

        T = models.Turn.objects.latest()
        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertEqual(
            2, T.unit_set.filter(standoff_from__isnull=False).count())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Vienna",
                              government__power__name="Italy",
                              displaced_from__name="Trieste",
                              u_type='A').exists())

        italy = models.Government.objects.get(power__name="Italy")
        vienna = models.Subregion.objects.get(territory__name="Vienna",
                                              sr_type="L")
        bohemia = models.Subregion.objects.get(territory__name="Bohemia",
                                               sr_type="L")

        self.assertTrue(
            not T.is_legal({'government': italy, 'turn': T,
                            'actor': vienna, 'action': "M",
                            'assist': None, 'target': bohemia}))
