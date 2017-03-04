from django.contrib.auth.models import User
import factory

from .. import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Faker('user_name')
    email = factory.Sequence(lambda n: 'user{}@example.com'.format(n))


class GameFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Game

    name = 'Test'
    slug = 'test'
    state = 'A'
    owner = factory.SubFactory(UserFactory)


class GovernmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Government
        django_get_or_create = ('power',)

    name = factory.Faker('first_name')
    user = factory.SubFactory(UserFactory)


class UnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Unit

    previous = ''


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Order

    assist = ''
    target = ''
