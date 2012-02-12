import models, forms
from django.test import TestCase
from django.db.models import Count
from django.core.management import call_command
from django.contrib.auth.models import User

import re
from collections import defaultdict

        # units = {}
        # T = models.Turn.objects.get()
        # create_units(units, T)

        # orders = {}
        # create_orders(orders, T)

convert = {'F': 'S', 'A': 'L'}
other = {'L': 'S', 'S': 'L', 'F': 'A', 'A': 'F'}

location = (r"(?{territory}[-\w.]{{2,}}(?: [-\w.]{{2,}})*)"
            r"(?: \((?{subname}\w+)\))?")
unit = r"(?{u_type}F|A) " + location
locRE = re.compile(location.format(territory="P<territory>",
                                   subname="P<subname>"))
unitRE = re.compile(unit.format(u_type="P<u_type>",
                                territory="P<territory>",
                                subname="P<subname>"))
unit_enhRE = re.compile(unit.format(u_type="P<u_type>",
                                    territory="P<territory>",
                                    subname="P<subname>") +
                        r"(?:, (displaced_from=[-\w.]+(?: [-\w.]+)*))?" +
                        r"(?:, (standoff_from=[-\w.]+(?: [-\w.]+)*))?")
opts = {'u_type': ':', 'territory': ':', 'subname': ':'}
U, L = unit.format(**opts), location.format(**opts)
order_patterns = {'H': re.compile(r"(?P<actor>{0}) H$".format(U)),
                  'M': re.compile(r"(?P<actor>{0}) M"
                                  r" (?P<target>{1})"
                                  r"(?: (?P<via_convoy>[*]))?$".format(U, L)),
                  'S': re.compile(r"(?P<actor>{0}) S (?P<assist>{0})"
                                  r"(?: - (?P<target>{1}))?$".format(U, L)),
                  'C': re.compile(r"(?P<actor>{0}) C (?P<assist>{0})"
                                  r" - (?P<target>{1})$".format(U, L)),
                  'B': re.compile(r"(?P<actor>{0}) B$".format(U)),
                  'D': re.compile(r"(?P<actor>{0}) D$".format(U))}

lookup = defaultdict(list)
for t in models.Territory.objects.all():
    for sr in t.subregion_set.all():
        lookup[(t.name,)].append(sr)
        lookup[(t.name, sr.subname or '')].append(sr)
        lookup[(t.name, sr.subname or '', sr.sr_type)].append(sr)

t_dict = dict((t.name, t.id) for t in models.Territory.objects.all())


def fetch(sr_type, territory, subname, strict=False):
    if sr_type in ('F', 'A'):
        sr_type = convert[sr_type]
    if subname is None:
        subname = ''
    if not lookup[(territory,)]:
        return
    if subname != '':
        if not lookup[(territory, subname)]:
            subname = ''

    result = lookup[(territory, subname, sr_type)]
    if not result and not strict:
        result = lookup[(territory, subname, other[sr_type])]
    if len(result) == 1:
        return result[0]

def create_unit(turn, gvt, unitstr):
    u = unit_enhRE.match(unitstr)
    kwargs = (group.split('=') for group in u.groups('') if '=' in group)
    kwargs = dict((g[0], territory[g[1]]) for g in kwargs)
    opts = u.groupdict('')
    return models.Unit.objects.create(u_type=opts['u_type'],
                                      subregion=fetch(opts['u_type'],
                                                      opts['territory'],
                                                      opts['subname']),
                                      turn=turn, government=gvt,
                                      **kwargs)

def create_units(units, turn):
    for gname, uset in units.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        for unit in uset:
            create_unit(turn, gvt, unit)

def split_unit(ustr, regexp=None):
    if regexp is None:
        regexp = unitRE
    u = regexp.match(ustr)
    if not u:
        return ('', '', '')
    return u.groups('')

def create_order(turn, gvt, orderstr):
    for action, regexp in order_patterns.iteritems():
        o = regexp.match(orderstr)
        if o is not None:
            break
    o_dict = o.groupdict('')
    actor = fetch(*split_unit(o_dict.get('actor', '')),
                   strict=(turn.season == 'FA'))
    assist = fetch(*split_unit(o_dict.get('assist', '')))
    sr_type = assist.sr_type if assist else (actor.sr_type if actor else '')
    target = fetch(sr_type, *split_unit(o_dict.get('target', ''), locRE)[:2])

    kwargs = {'actor': actor, 'action': action,
              'assist': assist, 'target': target,
              'via_convoy': bool(o_dict.get('via_convoy'))}

    return models.Order(turn=turn, government=gvt, **kwargs)

def create_orders(orders, turn):
    for gname, oset in orders.iteritems():
        gvt = models.Government.objects.get(power__name__startswith=gname)
        new_orders = [create_order(turn, gvt, order) for order in oset]
        for i, o in enumerate(sorted(new_orders, key=lambda x: x.actor_id)):
            o.slot = i
            o.save()


options = {'commit': False, 'verbosity': 0}

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


class BasicChecks(TestCase):
    """
    Based on section 6.A from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.A

    """

    fixtures = ['basic_game.json']

    def test_non_adjacent_move(self):
        # DATC 6.A.1
        units = {"England": ("F North Sea",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea M Picardy",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_army_to_sea(self):
        # DATC 6.A.2
        units = {"England": ("A Liverpool",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Irish Sea",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_fleet_to_land(self):
        # DATC 6.A.3
        units = {"Germany": ("F Kiel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Kiel M Munich",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_move_to_own_sector(self):
        # DATC 6.A.4
        units = {"Germany": ("F Kiel",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F Kiel M Kiel",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

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
        units = {"England": ("F London",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Germany": ("F London M North Sea",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    def test_only_armies_can_be_convoyed(self):
        # DATC 6.A.7
        units = {"England": ("F London",
                             "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London M Belgium",
                              "F North Sea C F London - Belgium")}
        create_orders(orders, T)

        orders = models.Order.objects.all()

        self.assertTrue(not T.is_legal(orders.get(slot=0)))
        self.assertTrue(not T.is_legal(orders.get(slot=1)))

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
        units = {"Italy": ("F Rome",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Italy": ("F Rome M Venice",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

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

        order = models.Order.objects.get(
            actor__territory__name="Rome")

        self.assertTrue(not T.is_legal(order))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            not T.unit_set.filter(displaced_from__isnull=False).exists())

    def test_simple_bounce(self):
        # DATC 6.A.11
        units = {"Austria": ("A Vienna",),
                 "Italy": ("A Venice",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Vienna M Tyrolia",),
                  "Italy": ("A Venice M Tyrolia",)}
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
        units = {"Austria": ("A Vienna",),
                 "Germany": ("A Munich",),
                 "Italy": ("A Venice",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Austria": ("A Vienna M Tyrolia",),
                  "Germany": ("A Munich M Tyrolia",),
                  "Italy": ("A Venice M Tyrolia",)}
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

    Several of these tests are inverted, since the engine is stricter
    than specified by the DATC.

    """

    fixtures = ['basic_game.json']

    def test_move_to_unspecified_coast_when_necessary(self):
        # DATC 6.B.1
        units = {"France": ("F Portugal",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Portugal M Spain",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

    # expected fail
    def test_move_to_unspecified_coast_when_unnecessary(self):
        # DATC 6.B.2
        units = {"France": ("F Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Gascony M Spain",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        # self.assertTrue(T.is_legal(order))
        self.assertTrue(not T.is_legal(order))

    def test_moving_to_wrong_but_unnecessary_coast(self):
        # DATC 6.B.3
        units = {"France": ("F Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Gascony M Spain (SC)",)}
        create_orders(orders, T)

        order = models.Order.objects.get()
        self.assertTrue(not T.is_legal(order))

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
        units = {"France": ("F Marseilles", "F Spain (NC)"),
                 "Italy": ("F Gulf of Lyon",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Marseilles M Gulf of Lyon",
                             "F Spain (NC) S F Marseilles - Gulf of Lyon"),
                  "Italy": ("F Gulf of Lyon H",)}
        create_orders(orders, T)

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Mid-Atlantic Ocean",
                              displaced_from__name="North Atlantic Ocean"
                              ).exists())

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

        # for o in models.Order.objects.all():
        #     self.assertTrue(T.is_legal(o))
        for o in models.Order.objects.exclude(actor__territory__name=
                                              "Portugal"):
            self.assertTrue(T.is_legal(o))

        self.assertTrue(not T.is_legal(
                models.Order.objects.get(actor__territory__name="Portugal")))

        T.game.generate()
        T = T.game.current_turn()

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name=
        #                       "Mid-Atlantic Ocean").exists())

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name=
        #                       "Western Mediterranean").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              government__power__name="Italy").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name=
                              "Mid-Atlantic Ocean").exists())

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

        # for o in models.Order.objects.all():
        #     self.assertTrue(T.is_legal(o))
        for o in models.Order.objects.exclude(actor__territory__name=
                                              "Portugal"):
            self.assertTrue(T.is_legal(o))

        self.assertTrue(not T.is_legal(
                models.Order.objects.get(actor__territory__name="Portugal")))

        T.game.generate()
        T = T.game.current_turn()

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name="Gascony").exists())

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name=
        #                       "Western Mediterranean").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              government__power__name="Italy").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Gascony").exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name=
        #                       "Mid-Atlantic Ocean").exists())

        # self.assertTrue(
        #     T.unit_set.filter(subregion__territory__name=
        #                       "Western Mediterranean").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name=
                              "Mid-Atlantic Ocean").exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Spain",
                              government__power__name="Italy").exists())

    # expected fail
    def test_unit_ordered_with_wrong_coast(self):
        # DATC 6.B.10
        units = {"France": ("F Spain (SC)",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Spain (NC) M Gulf of Lyon",)}
        create_orders(orders, T)

        o = models.Order.objects.get()
        # self.assertTrue(T.is_legal(o))
        self.assertTrue(not T.is_legal(o))

    def test_coast_cannot_be_ordered_to_change(self):
        # DATC 6.B.11
        units = {"France": ("F Spain (NC)",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("F Spain (SC) M Gulf of Lyon",)}
        create_orders(orders, T)

        o = models.Order.objects.get()
        self.assertTrue(not T.is_legal(o))

    # expected fail
    def test_army_movement_with_coastal_specification(self):
        # DATC 6.B.12
        units = {"France": ("A Gascony",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Gascony M Spain (NC)",)}
        create_orders(orders, T)

        o = models.Order.objects.get()
        # self.assertTrue(T.is_legal(o))
        self.assertTrue(not T.is_legal(o))

    def test_coastal_crawl_not_allowed(self):
        # DATC 6.B.13
        units = {"Turkey": ("F Bulgaria (SC)", "F Constantinople")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Bulgaria (SC) M Constantinople",
                             "F Constantinople M Bulgaria (EC)")}
        create_orders(orders, T)

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

    def test_build_with_unspecified_coast(self):
        # DATC 6.B.14
        T = models.Turn.objects.get()

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

        gvt = models.Government.objects.get(power__name="Russia")
        self.assertEqual(gvt.builds_available(), 4)
        o = models.Order.objects.get()
        self.assertIsNone(o.actor)
        self.assertTrue(T.is_legal(o))

        T.game.generate() # S 1901
        T = T.game.current_turn()

        self.assertTrue(not T.unit_set.exists())


class CircularMovement(TestCase):
    """
    Based on section 6.C from the Diplomacy Adjudicator Test Cases
    website.

    http://web.inter.nl.net/users/L.B.Kruijswijk/#6.C

    """

    fixtures = ['basic_game.json']

    def test_three_unit_circular_move(self):
        # DATC 6.C.1
        units = {"Turkey": ("F Ankara", "A Constantinople", "A Smyrna")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("F Ankara M Constantinople",
                             "A Constantinople M Smyrna",
                             "A Smyrna M Ankara")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              previous__subregion__territory__name="Ankara",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              previous__subregion__territory__name=
                              "Constantinople", u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              previous__subregion__territory__name="Smyrna",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              previous__subregion__territory__name="Ankara",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              previous__subregion__territory__name=
                              "Constantinople", u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              previous__subregion__territory__name="Smyrna",
                              u_type='A').exists())

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

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ankara",
                              previous__subregion__territory__name="Ankara",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              previous__subregion__territory__name=
                              "Constantinople", u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Smyrna",
                              previous__subregion__territory__name="Smyrna",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              previous__subregion__territory__name="Bulgaria",
                              u_type='A').exists())

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
                              previous__subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

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
                              previous__subregion__territory__name="Trieste",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Serbia",
                              previous__subregion__territory__name="Serbia",
                              government__power__name="Austria-Hungary",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Bulgaria",
                              previous__subregion__territory__name="Bulgaria",
                              government__power__name="Turkey",
                              u_type='A').exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=False).exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=False).exists())

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
                              displaced_from__isnull=False).exists())

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
                              displaced_from__isnull=False).exists())

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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=False,
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
                              displaced_from__isnull=False,
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
                              displaced_from__isnull=False,
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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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

        for o in models.Order.objects.filter(government__power__name=
                                             "Germany"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.filter(government__power__name=
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

        for o in models.Order.objects.filter(government__power__name=
                                             "France"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True).exists())

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

        for o in models.Order.objects.filter(government__power__name=
                                             "Russia"):
            self.assertTrue(not T.is_legal(o))
        for o in models.Order.objects.exclude(government__power__name=
                                              "Russia"):
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Constantinople",
                              government__power__name="Russia",
                              displaced_from__isnull=True).exists())

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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="France",
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
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
                              displaced_from__isnull=True,
                              u_type='F').exists())

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
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
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
        units = {"England": ("A Liverpool",),
                 "Russia": ("F Edinburgh",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A Liverpool M Edinburgh",),
                  "Russia": ("F Edinburgh M Liverpool",)}
        create_orders(orders, T)

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
        units = {"Turkey": ("A Greece", "F Aegean Sea",
                            "F Constantinople", "F Black Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Turkey": ("A Greece M Sevastopol",
                             "F Aegean Sea C A Greece - Sevastopol",
                             "F Constantinople C A Greece - Sevastopol",
                             "F Black Sea C A Greece - Sevastopol")}
        create_orders(orders, T)

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
        units = {"England": ("F English Channel", "A London"),
                 "France": ("A Paris",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F English Channel C A London - Brest",
                              "A London M Brest"),
                  "France": ("A Paris M Brest",)}
        create_orders(orders, T)

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
        units = {"England": ("F English Channel", "A London",
                             "F Mid-Atlantic Ocean"),
                 "France": ("A Paris",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F English Channel C A London - Brest",
                              "A London M Brest",
                              "F Mid-Atlantic Ocean S A London - Brest"),
                  "France": ("A Paris M Brest",)}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              previous__subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Paris",
                              government__power__name="France",
                              u_type='A').exists())

    def test_attacked_convoy_is_not_disrupted(self):
        # DATC 6.F.4
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Skagerrak",)}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Skagerrak M North Sea",)}
        create_orders(orders, T)

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
                              previous__subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_beleaguered_convoy_is_not_disrupted(self):
        # DATC 6.F.5
        units = {"England": ("F North Sea", "A London"),
                 "France": ("F English Channel", "F Belgium"),
                 "Germany": ("F Skagerrak", "F Denmark")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "France": ("F English Channel M North Sea",
                             "F Belgium S F English Channel - North Sea"),
                  "Germany": ("F Skagerrak M North Sea",
                              "F Denmark S F Skagerrak - North Sea")}
        create_orders(orders, T)

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
                              previous__subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="English Channel",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_dislodged_convoy_does_not_cut_support(self):
        # DATC 6.F.6
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("A Holland", "A Belgium",
                             "F Helgoland Bight", "F Skagerrak"),
                 "France": ("A Picardy", "A Burgundy")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("A Holland S A Belgium",
                              "A Belgium S A Holland",
                              "F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea"),
                  "France": ("A Picardy M Belgium",
                             "A Burgundy S A Picardy - Belgium")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_dislodged_convoy_does_not_cause_contested_area(self):
        # DATC 6.F.7
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Helgoland Bight", "F Skagerrak")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        orders = {"England": ("F North Sea M Holland",)}
        create_orders(orders, T)
        order = T.order_set.get()
        self.assertTrue(T.is_legal(order))

    def test_dislodged_convoy_does_not_cause_a_bounce(self):
        # DATC 6.F.8
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F Helgoland Bight", "F Skagerrak", "A Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Holland",
                              "A London M Holland"),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea",
                              "A Belgium M Holland")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Holland",
                              government__power__name="Germany",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy(self):
        # DATC 6.F.9
        units = {"England": ("F English Channel", "F North Sea", "A London"),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F English Channel C A London - Belgium",
                              "F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name=
                              "Mid-Atlantic Ocean",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy_with_foreign_fleet(self):
        # DATC 6.F.10
        units = {"England": ("F North Sea", "A London"),
                 "Germany": ("F English Channel",),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium"),
                  "Germany": ("F English Channel C A London - Belgium",),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name=
                              "Mid-Atlantic Ocean",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodge_of_multi_route_convoy_with_only_foreign_fleets(self):
        # DATC 6.F.11
        units = {"England": ("A London",),
                 "Germany": ("F English Channel",),
                 "Russia": ("F North Sea",),
                 "France": ("F Brest", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A London M Belgium",),
                  "Germany": ("F English Channel C A London - Belgium",),
                  "Russia": ("F North Sea C A London - Belgium",),
                  "France":
                      ("F Brest S F Mid-Atlantic Ocean - English Channel",
                       "F Mid-Atlantic Ocean M English Channel")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name=
                              "Mid-Atlantic Ocean",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_dislodged_convoying_fleet_not_on_route(self):
        # DATC 6.F.12
        units = {"England": ("F English Channel", "A London", "F Irish Sea"),
                 "France": ("F North Atlantic Ocean", "F Mid-Atlantic Ocean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F English Channel C A London - Belgium",
                              "A London M Belgium",
                              "F Irish Sea C A London - Belgium"),
                  "France": ("F North Atlantic Ocean S F Mid-Atlantic Ocean"
                             " - Irish Sea",
                             "F Mid-Atlantic Ocean M Irish Sea")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="Irish Sea",
                              previous__subregion__territory__name=
                              "Mid-Atlantic Ocean",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="England",
                              u_type='A').exists())

    def test_the_unwanted_alternative(self):
        # DATC 6.F.13
        units = {"England": ("A London", "F North Sea"),
                 "France": ("F English Channel",),
                 "Germany": ("F Holland", "F Denmark")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("A London M Belgium",
                              "F North Sea C A London - Belgium"),
                  "France": ("F English Channel C A London - Belgium",),
                  "Germany": ("F Holland S F Denmark - North Sea",
                              "F Denmark M North Sea")}
        create_orders(orders, T)

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

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Denmark",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_simple_convoy_paradox(self):
        # DATC 6.F.14
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name="Wales",
                              government__power__name="England",
                              u_type='F').exists())

    def test_simple_convoy_paradox_with_additional_convoy(self):
        # DATC 6.F.15
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel"),
                 "Italy": ("F Irish Sea", "F Mid-Atlantic Ocean",
                           "A North Africa")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Italy": ("F Irish Sea C A North Africa - Wales",
                            "F Mid-Atlantic Ocean C A North Africa - Wales",
                            "A North Africa M Wales")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name="Wales",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Wales",
                              government__power__name="Italy",
                              u_type='A').exists())

    def test_pandins_paradox(self):
        # DATC 6.F.16
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F North Sea", "F Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Germany": ("F North Sea S F Belgium - English Channel",
                              "F Belgium M English Channel")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Wales",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              displaced_from__isnull=True,
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
        units = {"England": ("F London", "F Wales"),
                 "France": ("A Brest", "F English Channel", "F Yorkshire"),
                 "Germany": ("F North Sea", "F Belgium")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F London S F Wales - English Channel",
                              "F Wales M English Channel"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London",
                             "F Yorkshire S A Brest - London"),
                  "Germany": ("F North Sea S F Belgium - English Channel",
                              "F Belgium M English Channel")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Belgium",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Wales",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="London",
                              government__power__name="England",
                              displaced_from__isnull=True,
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
        units = {"England": ("F North Sea", "A London", "F English Channel"),
                 "France": ("F Belgium",),
                 "Germany": ("F Helgoland Bight", "F Skagerrak")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F North Sea C A London - Belgium",
                              "A London M Belgium",
                              "F English Channel S A London - Belgium"),
                  "France": ("F Belgium S F North Sea",),
                  "Germany": ("F Helgoland Bight S F Skagerrak - North Sea",
                              "F Skagerrak M North Sea")}
        create_orders(orders, T)

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
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="England",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Skagerrak",
                              government__power__name="Germany",
                              u_type='F').exists())

    def test_multi_route_convoy_disruption_paradox(self):
        # DATC 6.F.19
        units = {"France": ("A Tunisia", "F Tyrrhenian Sea", "F Ionian Sea"),
                 "Italy": ("F Naples", "F Rome")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Tunisia M Naples",
                             "F Tyrrhenian Sea C A Tunisia - Naples",
                             "F Ionian Sea C A Tunisia - Naples"),
                  "Italy": ("F Naples S F Rome - Tyrrhenian Sea",
                            "F Rome M Tyrrhenian Sea")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="Naples",
                              government__power__name="Italy",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Rome",
                              government__power__name="Italy",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Tunisia",
                              government__power__name="France",
                              u_type='A').exists())

    def test_unwanted_multi_route_convoy_paradox(self):
        # DATC 6.F.20
        units = {"France": ("A Tunisia", "F Tyrrhenian Sea"),
                 "Italy": ("F Naples", "F Ionian Sea"),
                 "Turkey": ("F Aegean Sea", "F Eastern Mediterranean")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"France": ("A Tunisia M Naples",
                             "F Tyrrhenian Sea C A Tunisia - Naples"),
                  "Italy": ("F Naples S F Ionian Sea",
                            "F Ionian Sea C A Tunisia - Naples"),
                  "Turkey":
                      ("F Aegean Sea S F Eastern Mediterranean - Ionian Sea",
                       "F Eastern Mediterranean M Ionian Sea")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              government__power__name="Italy",
                              displaced_from__name="Eastern Mediterranean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Ionian Sea",
                              previous__subregion__territory__name=
                              "Eastern Mediterranean",
                              government__power__name="Turkey",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Tunisia",
                              government__power__name="France",
                              u_type='A').exists())

    def test_dads_army(self):
        # DATC 6.F.21
        units = {"Russia": ("A Edinburgh", "F Norwegian Sea", "A Norway"),
                 "France": ("F Irish Sea", "F Mid-Atlantic Ocean"),
                 "England": ("A Liverpool", "F North Atlantic Ocean",
                             "F Clyde")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"Russia": ("A Edinburgh S A Norway - Clyde",
                             "F Norwegian Sea C A Norway - Clyde",
                             "A Norway M Clyde"),
                  "France": ("F Irish Sea S F Mid-Atlantic Ocean"
                             " - North Atlantic Ocean",
                             "F Mid-Atlantic Ocean M North Atlantic Ocean"),
                  "England": ("A Liverpool M Clyde *", # via convoy
                              "F North Atlantic Ocean C A Liverpool - Clyde",
                              "F Clyde S F North Atlantic Ocean")}
        create_orders(orders, T)

        for o in models.Order.objects.all():
            self.assertTrue(T.is_legal(o))

        T.game.generate()
        T = T.game.current_turn()

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Atlantic Ocean",
                              government__power__name="England",
                              displaced_from__name="Mid-Atlantic Ocean",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Atlantic Ocean",
                              previous__subregion__territory__name=
                              "Mid-Atlantic Ocean",
                              government__power__name="France",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Clyde",
                              government__power__name="England",
                              displaced_from__name="Norway",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Clyde",
                              previous__subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_second_order_paradox_with_two_solutions(self):
        # DATC 6.F.22
        units = {"England": ("F Edinburgh", "F London"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F Belgium", "F Picardy"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

        orders = {"England": ("F Edinburgh M North Sea",
                              "F London S F Edinburgh - North Sea"),
                  "France": ("A Brest M London",
                             "F English Channel C A Brest - London"),
                  "Germany": ("F Belgium S F Picardy - English Channel",
                              "F Picardy M English Channel"),
                  "Russia": ("A Norway M Belgium",
                             "F North Sea C A Norway - Belgium")}
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="English Channel",
                              previous__subregion__territory__name="Picardy",
                              government__power__name="Germany",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__name="Edinburgh",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Edinburgh",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Brest",
                              government__power__name="France",
                              u_type='A').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Norway",
                              government__power__name="Russia",
                              u_type='A').exists())

    def test_second_order_paradox_with_two_exclusive_convoys(self):
        # DATC 6.F.23
        units = {"England": ("F Edinburgh", "F Yorkshire"),
                 "France": ("A Brest", "F English Channel"),
                 "Germany": ("F Belgium", "F London"),
                 "Italy": ("F Mid-Atlantic Ocean", "F Irish Sea"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

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
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="Mid-Atlantic Ocean",
                              government__power__name="Italy",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__isnull=True,
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="Edinburgh",
                              government__power__name="England",
                              u_type='F').exists())

    def test_second_order_paradox_with_no_resolution(self):
        # DATC 6.F.24
        units = {"England": ("F Edinburgh", "F London", "F Irish Sea",
                             "F Mid-Atlantic Ocean"),
                 "France": ("A Brest", "F English Channel", "F Belgium"),
                 "Russia": ("A Norway", "F North Sea")}
        T = models.Turn.objects.get()
        create_units(units, T)

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
        create_orders(orders, T)

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
            T.unit_set.filter(subregion__territory__name="Irish Sea",
                              government__power__name="England",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              government__power__name="Russia",
                              displaced_from__name="Edinburgh",
                              u_type='F').exists())

        self.assertTrue(
            T.unit_set.filter(subregion__territory__name="North Sea",
                              previous__subregion__territory__name="Edinburgh",
                              government__power__name="England",
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

        # Germany's armies have stood themselves off.
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
