from django.test import TestCase
from django.utils import six

from .. import models
from . import factories


if six.PY2:
    TestCase.assertCountEqual = six.assertCountEqual


class TurnTest(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(state='S')
        for x in range(7):
            factories.GovernmentFactory(game=self.game)
        self.assertTrue(self.game.activate())

    def test_recent_orders_spring(self):
        gvt = models.Government.objects.all()[0]

        t = factories.TurnFactory(game=self.game, year=1900, season='SR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='paris.l', previous='burgundy.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='paris.l', action='M', target='gascony.l')

        t = factories.TurnFactory(game=self.game, year=1900, season='F')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='gascony.l', previous='paris.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='gascony.l', action='M', target='marseilles.l')

        t = factories.TurnFactory(game=self.game, year=1900, season='FR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='marseilles.l', previous='gascony.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='marseilles.l', action='M', target='piedmont.l')

        t = factories.TurnFactory(game=self.game, year=1900, season='FA')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='B')

        t = factories.TurnFactory(game=self.game, year=1901, season='S')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='M', target='picardy.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='piedmont.l', action='M', target='tuscany.l')

        recent = t.recent_orders()
        self.assertEqual(len(recent), 1)
        power, orders = recent[0]
        self.assertEqual(power, gvt.power_display)
        self.assertEqual(len(orders), 2)
        (actor1, orders1), (actor2, orders2) = orders
        self.assertCountEqual([actor1, actor2], ['b.brest.l', 'gascony.l'])
        orders = {actor1: orders1, actor2: orders2}
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['b.brest.l']],
                         [('FA', 1900)])
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['gascony.l']],
                         [('F', 1900), ('FR', 1900)])

    def test_recent_orders_spring_retreat(self):
        gvt = models.Government.objects.all()[0]

        t = factories.TurnFactory(game=self.game, year=1900, season='FA')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='B')

        t = factories.TurnFactory(game=self.game, year=1901, season='S')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='B',
            actor='brest.l', action='M', target='picardy.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='piedmont.l', action='M', target='tuscany.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='SR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='M', target='paris.l')

        recent = t.recent_orders()
        self.assertEqual(len(recent), 1)
        power, orders = recent[0]
        self.assertEqual(power, gvt.power_display)
        self.assertEqual(len(orders), 2)
        (actor1, orders1), (actor2, orders2) = orders
        self.assertCountEqual([actor1, actor2], ['brest.l', 'piedmont.l'])
        orders = {actor1: orders1, actor2: orders2}
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['brest.l']],
                         [('S', 1901)])
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['piedmont.l']],
                         [('S', 1901)])

    def test_recent_orders_fall(self):
        gvt = models.Government.objects.all()[0]

        t = factories.TurnFactory(game=self.game, year=1900, season='FA')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='B')

        t = factories.TurnFactory(game=self.game, year=1901, season='S')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='piedmont.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='B',
            actor='brest.l', action='M', target='picardy.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='piedmont.l', action='M', target='tuscany.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='SR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='M', target='paris.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='F')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='paris.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='tuscany.l', action='M', target='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='paris.l', action='M', target='burgundy.l')

        recent = t.recent_orders()
        self.assertEqual(len(recent), 1)
        power, orders = recent[0]
        self.assertEqual(power, gvt.power_display)
        self.assertEqual(len(orders), 2)
        (actor1, orders1), (actor2, orders2) = orders
        self.assertCountEqual([actor1, actor2], ['brest.l', 'piedmont.l'])
        orders = {actor1: orders1, actor2: orders2}
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['brest.l']],
                         [('S', 1901), ('SR', 1901)])
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['piedmont.l']],
                         [('S', 1901)])

    def test_recent_orders_fall_retreat(self):
        gvt = models.Government.objects.all()[0]

        t = factories.TurnFactory(game=self.game, year=1901, season='SR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='M', target='paris.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='F')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='paris.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='B',
            actor='tuscany.l', action='M', target='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='paris.l', action='M', target='burgundy.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='FR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='burgundy.l', previous='paris.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='tuscany.l', action='M', target='rome.l')

        recent = t.recent_orders()
        self.assertEqual(len(recent), 1)
        power, orders = recent[0]
        self.assertEqual(power, gvt.power_display)
        self.assertEqual(len(orders), 2)
        (actor1, orders1), (actor2, orders2) = orders
        self.assertCountEqual([actor1, actor2], ['paris.l', 'tuscany.l'])
        orders = {actor1: orders1, actor2: orders2}
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['paris.l']],
                         [('F', 1901)])
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['tuscany.l']],
                         [('F', 1901)])

    def test_recent_orders_fall_adjustment(self):
        gvt = models.Government.objects.all()[0]

        t = factories.TurnFactory(game=self.game, year=1901, season='SR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='brest.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='piedmont.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='brest.l', action='M', target='paris.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='F')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='paris.l', previous='brest.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='B',
            actor='tuscany.l', action='M', target='marseilles.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='paris.l', action='M', target='burgundy.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='FR')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='burgundy.l', previous='paris.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='tuscany.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='tuscany.l', action='M', target='rome.l')

        t = factories.TurnFactory(game=self.game, year=1901, season='FA')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='burgundy.l', previous='burgundy.l')
        factories.UnitFactory(
            turn=t, government=gvt, u_type='A',
            subregion='rome.l', previous='tuscany.l')
        factories.CanonicalOrderFactory(
            turn=t, government=gvt, result='S',
            actor='marseilles.l', action='B')

        recent = t.recent_orders()
        self.assertEqual(len(recent), 1)
        power, orders = recent[0]
        self.assertEqual(power, gvt.power_display)
        self.assertEqual(len(orders), 2)
        (actor1, orders1), (actor2, orders2) = orders
        self.assertCountEqual([actor1, actor2], ['paris.l', 'tuscany.l'])
        orders = {actor1: orders1, actor2: orders2}
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['paris.l']],
                         [('F', 1901)])
        self.assertEqual([(o.turn.season, o.turn.year) for o in orders['tuscany.l']],
                         [('F', 1901), ('FR', 1901)])
