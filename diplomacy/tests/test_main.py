from django.test import TestCase
from django.utils import six

from ..engine import main


if six.PY2:
    TestCase.assertCountEqual = six.assertCountEqual


class UpdateOwnershipTest(TestCase):
    def test_unoccupied(self):
        units = []
        owns = [{'territory': 'paris', 'government': 'france'}]

        new_owns = main.update_ownership(units, owns)

        self.assertCountEqual(new_owns, [{'territory': 'paris', 'government': 'france'}])

    def test_army(self):
        units = [
            {'government': 'france',
             'u_type': 'A',
             'subregion': 'spain.l',
             'previous': 'marseilles.l',
             'dislodged': False,
             'displaced_from': '',
             'standoff_from': ''}
        ]
        owns = []

        new_owns = main.update_ownership(units, owns)

        self.assertCountEqual(new_owns, [{'territory': 'spain', 'government': 'france'}])

    def test_fleet(self):
        units = [
            {'government': 'england',
             'u_type': 'F',
             'subregion': 'norway.s',
             'previous': 'norwegian-sea.s',
             'dislodged': False,
             'displaced_from': '',
             'standoff_from': ''}
        ]
        owns = []

        new_owns = main.update_ownership(units, owns)

        self.assertCountEqual(new_owns, [{'territory': 'norway', 'government': 'england'}])

    def test_fleet_on_coast(self):
        units = [
            {'government': 'austria-hungary',
             'u_type': 'F',
             'subregion': 'bulgaria.sc.s',
             'previous': 'greece.s',
             'dislodged': False,
             'displaced_from': '',
             'standoff_from': ''}
        ]
        owns = []

        new_owns = main.update_ownership(units, owns)

        self.assertCountEqual(new_owns,
                              [{'territory': 'bulgaria', 'government': 'austria-hungary'}])

    def test_fleet_on_sea(self):
        units = [
            {'government': 'italy',
             'u_type': 'F',
             'subregion': 'ionian-sea.s',
             'previous': 'naples.s',
             'dislodged': False,
             'displaced_from': '',
             'standoff_from': ''}
        ]
        owns = []

        new_owns = main.update_ownership(units, owns)

        self.assertCountEqual(new_owns, [])


class IncrementTurnTest(TestCase):
    def test_spring(self):
        turn = main.increment_turn({
            'number': 0,
            'year': 1900,
            'season': 'S'
        })

        self.assertEqual(turn, {
            'number': 1,
            'year': 1900,
            'season': 'SR'
        })

    def test_spring_retreat(self):
        turn = main.increment_turn({
            'number': 1,
            'year': 1900,
            'season': 'SR'
        })

        self.assertEqual(turn, {
            'number': 2,
            'year': 1900,
            'season': 'F'
        })

    def test_fall(self):
        turn = main.increment_turn({
            'number': 2,
            'year': 1900,
            'season': 'F'
        })

        self.assertEqual(turn, {
            'number': 3,
            'year': 1900,
            'season': 'FR'
        })

    def test_fall_retreat(self):
        turn = main.increment_turn({
            'number': 3,
            'year': 1900,
            'season': 'FR'
        })

        self.assertEqual(turn, {
            'number': 4,
            'year': 1900,
            'season': 'FA'
        })

    def test_fall_adjustment(self):
        turn = main.increment_turn({
            'number': 4,
            'year': 1900,
            'season': 'FA'
        })

        self.assertEqual(turn, {
            'number': 5,
            'year': 1901,
            'season': 'S'
        })
