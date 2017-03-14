from django.contrib.auth.models import User
import factory

from .. import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Faker('user_name')
    email = factory.Sequence(lambda n: 'user{}@example.com'.format(n))


class GameFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Game
        django_get_or_create = ('slug',)

    name = 'Test'
    slug = 'test'
    state = 'A'
    owner = factory.SubFactory(UserFactory)


class TurnFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Turn

    game = factory.SubFactory(GameFactory)
    year = 1900
    season = 'S'

    @factory.lazy_attribute
    def number(self):
        seasons = [s for s, sname in models.SEASON_CHOICES]
        return 5 * (self.year - 1900) + seasons.index(self.season)


class GovernmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Government

    name = factory.Faker('first_name')
    user = factory.SubFactory(UserFactory)
    power = ''


class UnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Unit

    previous = ''


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Order

    assist = ''
    target = ''


class CanonicalOrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CanonicalOrder

    turn = factory.SubFactory(TurnFactory)
    government = factory.SubFactory(GovernmentFactory)

    via_convoy = False
    user_issued = True
