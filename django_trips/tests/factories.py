"""
🧪Test Cases for Django Models. 
"""

# pylint:disable=all

import random
from datetime import timedelta

import factory.fuzzy
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from faker import Faker
from rest_framework_simplejwt.tokens import AccessToken

from django_trips.choices import (
    BookingStatus,
    LocationType,
    ScheduleStatus,
    TripOptions,
)
from django_trips.models import (
    Category,
    Facility,
    Gear,
    Host,
    HostType,
    Location,
    Trip,
    TripBooking,
    TripItinerary,
    TripOption,
    TripSchedule,
)

USER_PASSWORD = "pswd"

fake = Faker()


class AuthenticatedUserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.access_token = AccessToken.for_user(cls.user)
        cls.headers = {"Authorization": f"Bearer {cls.access_token}"}

    def get_access_token_header_for_user(self, user):
        access_token = AccessToken.for_user(user)
        return {"Authorization": f"Bearer {access_token}"}


class GroupFactory(DjangoModelFactory):
    """Group factory"""

    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"group - {n}")


class UserFactory(DjangoModelFactory):
    """User factory"""

    username = factory.Sequence(lambda n: f"User - {n}")
    password = factory.PostGenerationMethodCall("set_password", USER_PASSWORD)

    class Meta:
        model = User
        django_get_or_create = ("username",)


class CategoryFactory(DjangoModelFactory):

    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Category - {n}")

    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    is_active = True


class GearFactory(DjangoModelFactory):
    """Gear factory"""

    class Meta:
        model = Gear
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Gear - {n}")

    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    is_active = True


class HostTypeFactory(DjangoModelFactory):
    class Meta:
        model = HostType
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"HostType - {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class HostFactory(DjangoModelFactory):
    class Meta:
        model = Host

    name = factory.Faker("company")
    description = factory.Faker("text")
    type = factory.SubFactory(HostTypeFactory)
    cnic = factory.Faker("numerify", text="###########")
    email = factory.Faker("email")
    mobile = factory.Faker("numerify", text="+92##########")
    address = factory.LazyAttribute(lambda o: fake.address()[:250])
    cancellation_policy = factory.LazyFunction(
        lambda: [
            {"policy": "Non-refundable", "days": 0},
            {"policy": "Refundable", "days": 7},
        ]
    )

    refund_policy = factory.LazyFunction(
        lambda: [
            {"policy": "Full refund", "days": 7},
            {"policy": "Partial refund", "days": 3},
        ]
    )
    verified = True


class FacilityFactory(DjangoModelFactory):

    class Meta:
        model = Facility
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Facility - {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    is_active = True


class LocationFactory(DjangoModelFactory):

    class Meta:
        model = Location
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Test Location {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    travel_tips = factory.LazyFunction(lambda: {"tip": "Bring sunscreen!"})
    lat = factory.LazyFunction(lambda: float(round(fake.latitude(), 6)))
    lon = factory.LazyFunction(lambda: float(round(fake.longitude(), 6)))
    type = factory.Iterator(LocationType.values)
    importance = factory.LazyFunction(lambda: round(random.uniform(0.1, 2.0), 2))
    is_active = True


class TripFactory(DjangoModelFactory):
    name = factory.Faker("sentence", nb_words=6)
    slug = factory.Faker("slug")
    description = factory.Faker("text")
    overview = factory.Faker("text")
    included = factory.Faker("text")
    excluded = factory.Faker("text")
    add_ons = factory.Faker("text")
    travel_tips = factory.LazyFunction(lambda: {"tip": "Always pack light"})
    requirements = factory.LazyFunction(lambda: {"requirement": "Valid passport"})
    child_policy = factory.LazyFunction(
        lambda: {"policy": "Children must be accompanied by an adult"}
    )

    duration = factory.Faker("time_delta", end_datetime="+30d")
    passenger_limit_min = factory.Faker("random_int", min=1, max=10)
    passenger_limit_max = factory.Faker("random_int", min=10, max=50)
    age_limit = factory.Faker("random_int", min=5, max=70)

    departure = factory.SubFactory(LocationFactory)
    destination = factory.SubFactory(LocationFactory)
    country = "PK"  # Use country code, assuming the default is 'PK'

    metadata = factory.LazyFunction(
        lambda: {
            "tinyurl": "http://example.com",
            "poster": "http://example.com/poster.jpg",
        }
    )

    is_featured = factory.Faker("boolean")
    is_pax_required = factory.Faker("boolean")
    is_active = True

    created_at = factory.Faker("date_time_this_decade")
    updated_at = factory.Faker("date_time_this_decade")

    created_by = factory.SubFactory(UserFactory)

    host = factory.SubFactory(HostFactory)
    tags = factory.LazyFunction(lambda: ["Adventure", "Mountain"])

    class Meta:
        model = Trip

    @factory.post_generation
    def facilities(self, create, extracted, **kwargs):
        handle_m2m_field(self, "facilities", FacilityFactory, create, extracted)

    @factory.post_generation
    def gear(self, create, extracted, **kwargs):
        handle_m2m_field(self, "gear", GearFactory, create, extracted)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        handle_m2m_field(self, "locations", LocationFactory, create, extracted)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        handle_m2m_field(self, "categories", CategoryFactory, create, extracted)

    @factory.post_generation
    def trip_schedule(self, create, number=1):
        """The post_generation decorator performs actions once the model object has been generated."""
        if number is None:
            return
        TripScheduleFactory.simple_generate_batch(create, trip=self, size=number)


def handle_m2m_field(instance, field_name, factory_cls, create, extracted, attr="name"):
    if not create:
        return
    if extracted and isinstance(extracted, list):
        extracted = [
            obj if not isinstance(obj, str) else factory_cls(**{attr: obj})
            for obj in extracted
        ]
    if extracted:
        getattr(instance, field_name).set(extracted)
    else:
        items = factory_cls.create_batch(3)
        getattr(instance, field_name).set(items)


class TripItineraryFactory(DjangoModelFactory):
    class Meta:
        model = TripItinerary

    trip = factory.SubFactory(TripFactory)
    day_index = factory.Sequence(lambda n: n + 1)
    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("paragraph", nb_sentences=4)
    location = factory.SubFactory(LocationFactory)
    category = factory.SubFactory(CategoryFactory)
    # pylint:disable=unnecessary-lambda
    start_time = factory.LazyFunction(lambda: timezone.now())
    end_time = factory.LazyAttribute(lambda o: o.start_time + timedelta(hours=3))


class TripOptionFactory(DjangoModelFactory):
    trip = factory.SubFactory(TripFactory)
    name = factory.Faker(
        "random_element", elements=[choice[0] for choice in TripOptions.choices]
    )
    description = factory.Faker("paragraph", nb_sentences=1)
    base_price = factory.Faker("random_int", min=0, max=100)
    base_child_price = factory.Faker("random_int", min=0, max=100)

    class Meta:
        model = TripOption


class TripScheduleFactory(DjangoModelFactory):
    class Meta:
        model = TripSchedule

    trip = factory.SubFactory(TripFactory)  # Generates a related Trip instance
    price = factory.Faker("random_number", digits=5)  # Random price
    is_per_person_price = factory.Faker("boolean")
    start_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=10))

    available_seats = factory.Faker("random_int", min=0, max=100)
    booked_seats = factory.Faker("random_int", min=0, max=100)
    status = factory.Faker(
        "random_element", elements=[choice[0] for choice in ScheduleStatus.choices]
    )


class TripBookingFactory(DjangoModelFactory):
    class Meta:
        model = TripBooking

    schedule = factory.SubFactory(TripScheduleFactory)
    full_name = factory.Faker("name")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    number_of_persons = factory.Faker("random_int", min=1, max=10)
    target_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=10))
    status = BookingStatus.PENDING  # Adjust based on your Enum/Choices
    created_by = factory.SubFactory(UserFactory)


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
        trip_schedule=trip_schedules,
    )
    return trip
