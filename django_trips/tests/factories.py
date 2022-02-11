from datetime import datetime

import factory.fuzzy
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Group, User
from factory.django import DjangoModelFactory
from pytz import UTC

from django_trips.models import (Category, Facility, Gear, Host, Location, Trip,
                                 TripItinerary, TripSchedule, HostType, )

USER_PASSWORD = 'pswd'


class GroupFactory(DjangoModelFactory):
    """Group factory"""

    class Meta(object):
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence("group{0}".format)


class UserFactory(DjangoModelFactory):
    """User factory"""

    username = factory.Sequence(u'User - {0}'.format)
    password = factory.PostGenerationMethodCall('set_password', USER_PASSWORD)

    class Meta:
        model = User
        django_get_or_create = ('username',)


class CategoryFactory(DjangoModelFactory):
    """Category factory"""

    class Meta(object):
        model = Category
        django_get_or_create = ('name',)

    name = factory.Sequence("Category - {0}".format)
    slug = factory.Sequence("category-{0}".format)


class GearFactory(DjangoModelFactory):
    """Gear factory"""

    class Meta(object):
        model = Gear
        django_get_or_create = ('name',)

    name = factory.Sequence("Gear - {0}".format)
    slug = factory.Sequence("gear-{0}".format)


class HostTypeFactory(DjangoModelFactory):
    class Meta:
        model = HostType
        django_get_or_create = ('name',)

    name = factory.Sequence("HostType - {0}".format)


class HostFactory(DjangoModelFactory):
    """Host factory"""

    class Meta(object):
        model = Host

    name = factory.Sequence("Host - {0}".format)
    cancellation_policy = factory.Sequence("cancellation Policy - {0}".format)
    type = factory.SubFactory(HostTypeFactory)


class FacilityFactory(DjangoModelFactory):
    """Facility factory"""

    class Meta(object):
        model = Facility
        django_get_or_create = ('name',)

    name = factory.Sequence("Facility - {0}".format)


class LocationFactory(DjangoModelFactory):
    """Location factory"""

    class Meta(object):
        model = Location
        django_get_or_create = ('name',)

    name = factory.Sequence("Location - {0}".format)


class TripScheduleFactory(DjangoModelFactory):
    """TripSchedule factory"""

    class Meta:
        model = TripSchedule

    date_from = factory.fuzzy.FuzzyDateTime(
        datetime.now(tz=UTC), datetime.now(tz=UTC) + relativedelta(months=+1)
    )


class TripItineraryFactory(DjangoModelFactory):
    class Meta:
        model = TripItinerary


class TripFactory(DjangoModelFactory):
    """Trip factory"""

    class Meta(object):
        model = Trip
        django_get_or_create = ("slug",)

    name = factory.Sequence("My awsome trip - {0}".format)
    slug = factory.Sequence("my-awsome-trip-{0}".format)
    description = factory.Sequence("awsome trip description- {}".format)

    destination = factory.SubFactory(LocationFactory)
    starting_location = factory.SubFactory(LocationFactory)
    locations = factory.SubFactory(LocationFactory)
    primary_category = factory.SubFactory(CategoryFactory)
    categories = factory.SubFactory(CategoryFactory)
    facilities = factory.SubFactory(FacilityFactory)
    trip_schedule = factory.SubFactory(TripScheduleFactory)

    gear = factory.SubFactory(GearFactory)

    created_by = factory.SubFactory(UserFactory)
    host = factory.SubFactory(HostFactory)

    created_at = datetime(2012, 1, 1, tzinfo=UTC)
    updated_at = datetime(2013, 1, 1, tzinfo=UTC)

    @factory.post_generation
    def locations(self, create, extracted):
        """The post_generation decorator performs actions once the model object has been generated."""
        for group_name in _as_list(extracted):
            self.locations.add(LocationFactory.simple_generate(create, name=group_name))

    @factory.post_generation
    def facilities(self, create, extracted):
        """The post_generation decorator performs actions once the model object has been generated."""

        for group_name in _as_list(extracted):
            self.facilities.add(FacilityFactory.simple_generate(create, name=group_name))

    @factory.post_generation
    def gear(self, create, extracted):
        """The post_generation decorator performs actions once the model object has been generated."""

        for group_name in _as_list(extracted):
            self.gear.add(GearFactory.simple_generate(create, name=group_name))

    @factory.post_generation
    def categories(self, create, extracted):
        """The post_generation decorator performs actions once the model object has been generated."""
        for group_name in _as_list(extracted):
            self.categories.add(CategoryFactory.simple_generate(create, name=group_name))

    @factory.post_generation
    def trip_schedule(self, create, number=1):
        """The post_generation decorator performs actions once the model object has been generated."""
        if number is None:
            return
        TripScheduleFactory.simple_generate_batch(create, trip=self, size=number)


def _as_list(extracted):
    if extracted is None:
        extracted = []
    elif isinstance(extracted, str):
        extracted = [extracted]
    return extracted


def get_trip(trip_schedules=2):
    trip = TripFactory.create(
        locations=["Lahore", "Gilgit"],
        facilities=["Transport", "Food"],
        gear=["Backpack", "Glasses"],
        categories=["Outdoors", "Hiking"],
        trip_schedule=trip_schedules
    )
    return trip
