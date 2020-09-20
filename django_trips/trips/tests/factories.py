from datetime import datetime

import factory
from django.contrib.auth.models import Group, User
from factory.django import DjangoModelFactory
from pytz import UTC

from trips.models import (
    Category, Facility, Host, Location, Trip, TripItinerary, TripSchedule
)


class GroupFactory(DjangoModelFactory):
    """Group factory"""

    class Meta(object):
        model = Group
        django_get_or_create = ('name',)

    name = factory.Sequence('group{0}'.format)


class UserFactory(DjangoModelFactory):
    """User factory"""

    class Meta:
        model = User


class CategoryFactory(DjangoModelFactory):
    """Category factory"""

    class Meta(object):
        model = Category

    name = factory.Sequence('Category - {0}'.format)
    slug = factory.Sequence('category-{0}'.format)


class HostFactory(DjangoModelFactory):
    """Host factory"""

    class Meta(object):
        model = Host

    name = factory.Sequence('Host - {0}'.format)
    cancellation_policy = factory.Sequence('cancellation Policy - {0}'.format)


class FacilityFactory(DjangoModelFactory):
    """Facility factory"""

    class Meta(object):
        model = Facility

    name = factory.Sequence('Facility - {0}'.format)


class LocationFactory(DjangoModelFactory):
    """Location factory"""

    class Meta(object):
        model = Location

    name = factory.Sequence('Location - {0}'.format)
    # is_destination = factory


class TripScheduleFactory(DjangoModelFactory):
    """TripSchedule factory"""

    class Meta:
        model = TripSchedule

    date_from = datetime(2012, 1, 1, tzinfo=UTC)


class TripItineraryFactory(DjangoModelFactory):
    class Meta:
        model = TripItinerary


class TripFactory(DjangoModelFactory):
    """Trip factory"""

    class Meta(object):
        model = Trip
        django_get_or_create = ('slug',)

    name = factory.Sequence('My awsome trip - {0}'.format)
    slug = factory.Sequence('my-awsome-trip-{0}'.format)
    description = factory.Sequence('awsome trip description- {}'.format)

    destination = factory.SubFactory(LocationFactory)
    locations = factory.SubFactory(LocationFactory)
    category = factory.SubFactory(CategoryFactory)
    facilities = factory.SubFactory(FacilityFactory)

    gear = factory.Sequence('Trip gear - {0}'.format)

    created_by = factory.SubFactory(UserFactory)
    host = factory.SubFactory(HostFactory)

    created_at = datetime(2012, 1, 1, tzinfo=UTC)
    updated_at = datetime(2011, 1, 1, tzinfo=UTC)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        """The post_generation decorator performs actions once the model object has been generated."""
        if extracted is None:
            return

        if isinstance(extracted, str):
            extracted = [extracted]

        for group_name in extracted:
            self.locations.add(LocationFactory.simple_generate(create, name=group_name))

    @factory.post_generation
    def facilities(self, create, extracted, **kwargs):
        """The post_generation decorator performs actions once the model object has been generated."""
        if extracted is None:
            return

        if isinstance(extracted, str):
            extracted = [extracted]

        for group_name in extracted:
            self.facilities.add(FacilityFactory.simple_generate(create, name=group_name))
