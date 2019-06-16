import re

from django.test import TestCase
from django.utils import six

from ..engine.digest import find_convoys
from ..engine.utils import (get_territory, territory_display, unit_display, subregion_token,
                            power_token)


if six.PY2:
    TestCase.assertCountEqual = six.assertCountEqual


convert = {'F': 'S', 'A': 'L'}
unitRE = re.compile(
    r"(?P<u_type>F|A) (?P<territory>[-\w.]{2,}(?: [-\w.]{2,})*)(?: \((?P<subname>\w+)\))?")


class CorrectnessHelperTest(TestCase):
    def parse_unit_subregion(self, unit):
        data = unitRE.match(unit).groupdict()
        return subregion_token(
            (data['territory'], data['subname'] or '', convert[data['u_type']])
        )

    def parse_units(self, units):
        return [
            {'government': power_token(g),
             'u_type': unitstr[0],
             'subregion': self.parse_unit_subregion(unitstr)}
            for g, uset in units.items()
            for unitstr in uset
        ]

    def test_find_convoys(self):
        units = {'England': ('F Mid-Atlantic Ocean',
                             'F English Channel',
                             'F Western Mediterranean',
                             'F Spain (NC)',    # coastal, can't participate
                             'F Ionian Sea',    # fake group
                             'F Adriatic Sea',  # fake group
                             'F Baltic Sea',
                             'F Gulf of Bothnia',
                             'A Gascony',
                             'A Sweden')}

        parsed = self.parse_units(units)
        fleets = [u['subregion'] for u in parsed if u['u_type'] == 'F']
        legal = find_convoys(parsed, fleets)

        self.assertEqual(len(legal), 2)
        (seas1, lands1), (seas2, lands2) = legal
        if len(seas1) == 2:
            seas1, seas2 = seas2, seas1
            lands1, lands2 = lands2, lands1

        self.assertEqual(len(seas1), 3)
        self.assertCountEqual(
            [unit_display(sr) for sr in seas1],
            units['England'][:3]
        )

        self.assertEqual(len(lands1), 10)
        self.assertCountEqual(
            [territory_display(get_territory(sr)) for sr in lands1],
            ['Tunisia', 'North Africa', 'London', 'Wales', 'Spain',
             'Brest', 'Gascony', 'Picardy', 'Belgium', 'Portugal']
        )

        self.assertEqual(len(seas2), 2)
        self.assertCountEqual(
            [unit_display(sr) for sr in seas2],
            units['England'][6:8]
        )

        self.assertEqual(len(lands2), 8)
        self.assertCountEqual(
            [territory_display(get_territory(sr)) for sr in lands2],
            ['Prussia', 'Berlin', 'Kiel', 'Denmark', 'Sweden',
             'Finland', 'St. Petersburg', 'Livonia']
        )
