from django.contrib.auth.models import User
import factory

from .. import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda a: '{}@example.com'.format(a))


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

    name = factory.Faker('first_name')
    user = factory.SubFactory(UserFactory)
