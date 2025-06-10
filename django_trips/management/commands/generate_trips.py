from datetime import datetime, timedelta, time
import random

from django.contrib.auth import get_user_model
from faker import Faker

import random
import traceback
from collections import namedtuple
from datetime import datetime, timedelta

from dateutil.tz import UTC
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from django_trips.choices import ScheduleStatus, TripOptions
from django_trips.models import (
    Category,
    Facility,
    Gear,
    Host,
    Location,
    Trip,
    TripItinerary,
    TripSchedule,
    HostType,
    TripOption,
)


fake = Faker()
User = get_user_model()

DEFAULT_SETTINGS = {
    "TRIP_DESTINATIONS": ["Boston", "London"],
    "TRIP_DEPARTURE_LOCATION": ["Boston"],
    "TRIP_LOCATIONS": ["Boston", "London", "Delhi"],
    "TRIP_HOSTS": ["Django"],
    "TRIP_HOST_TYPES": ["Tour Operator", "Individual"],
    "TRIP_FACILITIES": ["Bone-fire", "Food", "Drinks"],
    "TRIP_CATEGORIES": ["Honymoon", "Outdoor"],
    "TRIP_GEARS": ["Sun glasses", "Sun block"],
}


class Command(BaseCommand):
    """
    This command will generate batch of trips with random data.

    By running this command, the trips generated will have random data
    from a pre-defined list of data. The data selection is done at the
    random to ensure that trips will have diverse data, which will provide
    help for filtering & searching.

    EXAMPLE USAGE:
        ./manage.py generate_trips --batch_size=100
    OR
        ./manage.py generate_trips

    If batch size is not provided, the command will generate 10 trips
    """

    help = "Generate batches of trip with pre-populated random data"

    def add_arguments(self, parser):
        """
        Defining the arguments to be used by the command.
        """
        parser.add_argument(
            "--batch_size",
            type=int,
            default=10,
            dest="batch_size",
            help="number to trips to generate",
        )

    def get_setting(self, key):
        return getattr(settings, key, DEFAULT_SETTINGS.get(key, []))

    def handle(self, *args, **options):
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            raise CommandError(
                "No superuser found. Create one before generating trips."
            )

        for _ in range(options["batch_size"]):
            no_of_days = random.randint(5, 20)
            try:
                trip = self.create_trip(user, no_of_days)
                self.create_itineraries(trip, no_of_days)
                self.create_schedules(trip)
                self.create_trip_options(trip)
                self.stdout.write(
                    self.style.SUCCESS(f"Trip Created: <id={trip.pk} name={trip.name}>")
                )
            except Exception as e:
                self.stderr.write(traceback.format_exc())
                raise CommandError(f"Error creating trip: {e}")

    def create_trip(self, user, no_of_days):
        duration = timedelta(days=no_of_days)
        destination = self.get_location("TRIP_DESTINATIONS")
        departure = self.get_location("TRIP_DEPARTURE_LOCATION")
        name = f"{duration.days}-day trip to {destination.name}"

        trip = Trip(
            name=name,
            description=fake.paragraph(),
            duration=duration,
            destination=destination,
            departure=departure,
            age_limit=random.randint(20, 40),
            host=self.get_host(),
            overview=fake.text(),
            included=fake.text(),
            excluded=fake.text(),
            add_ons=fake.text(),
            travel_tips=[fake.sentence() for _ in range(3)],
            requirements=[fake.sentence() for _ in range(3)],
            child_policy=[fake.sentence() for _ in range(2)],
            passenger_limit_min=random.randint(1, 4),
            passenger_limit_max=random.randint(5, 15),
            created_by=user,
        )

        trip.save()

        trip.gear.set(self.get_gears())
        trip.locations.set(self.get_locations())
        trip.facilities.set(self.get_facilities())
        trip.categories.set(self.get_categories())
        trip.options.add()

        trip.tags.add("Adventure", "Group")
        return trip

    def create_schedules(self, trip):
        now = timezone.now()
        duration_days = trip.duration.days
        price_choices = [1000, 5000, 6000, 9000]

        # 1. Expired schedule
        TripSchedule.objects.create(
            trip=trip,
            start_date=now - timedelta(days=duration_days + 10),
            end_date=now - timedelta(days=5),
            price=random.choice(price_choices),
            status=ScheduleStatus.FULL,
        )
        # 2. In-progress schedule
        TripSchedule.objects.create(
            trip=trip,
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=duration_days),
            price=random.choice(price_choices),
            status=ScheduleStatus.PUBLISHED,
        )

        # 3. Upcoming schedule
        TripSchedule.objects.create(
            trip=trip,
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=5 + duration_days),
            price=random.choice(price_choices),
            status=ScheduleStatus.PUBLISHED,
        )

    def get_category(self):
        name = random.choice(self.get_setting("TRIP_CATEGORIES"))
        return Category.objects.get_or_create(
            name=name, defaults={"slug": slugify(name)}
        )[0]

    def get_categories(self):
        names = random.sample(self.get_setting("TRIP_CATEGORIES"), random.randint(1, 3))
        return [
            Category.objects.get_or_create(slug=slugify(name), defaults={"name": name})[
                0
            ]
            for name in names
        ]

    def create_trip_options(self, trip):
        names = random.sample(TripOptions.values, random.randint(1, 3))
        return [
            TripOption.objects.get_or_create(
                trip=trip, name=name, defaults={"description": name}
            )[0]
            for name in names
        ]

    def get_location(self, key):
        name = random.choice(self.get_setting(key))
        return self.get_or_create_model(Location, name)

    def get_locations(self):
        names = random.sample(self.get_setting("TRIP_LOCATIONS"), random.randint(1, 3))
        return [
            Location.objects.get_or_create(slug=slugify(name), defaults={"name": name})[
                0
            ]
            for name in names
        ]

    def get_facilities(self):
        names = random.sample(self.get_setting("TRIP_FACILITIES"), random.randint(1, 3))
        return [
            Facility.objects.get_or_create(name=name, defaults={"slug": slugify(name)})[
                0
            ]
            for name in names
        ]

    def get_host(self):
        name = random.choice(self.get_setting("TRIP_HOSTS"))
        host_type = self.get_host_type()
        return Host.objects.get_or_create(
            name=name, defaults=dict(verified=True, type=host_type)
        )[0]

    def get_host_type(self):
        name = random.choice(self.get_setting("TRIP_HOST_TYPES"))
        return HostType.objects.get_or_create(
            name=name, defaults={"slug": slugify(name)}
        )[0]

    def get_gears(self):
        names = random.sample(self.get_setting("TRIP_GEARS"), random.randint(1, 3))
        return [
            Gear.objects.get_or_create(name=name, defaults={"slug": slugify(name)})[0]
            for name in names
        ]

    def get_or_create_model(self, model, name):
        slug = slugify(name)
        return model.objects.get_or_create(slug=slug, defaults={"name": name})[0]

    def get_or_create_multiple(self, key, model):
        names = random.sample(
            self.get_setting(key), random.randint(1, len(self.get_setting(key)))
        )
        return [self.get_or_create_model(model, name) for name in names]

    def create_itineraries(self, trip, no_of_days):
        for day, itinerary in enumerate(self.generate_itineraries(no_of_days), start=1):
            TripItinerary.objects.create(trip=trip, day_index=day, **itinerary)

    def generate_itineraries(self, no_of_days=None):
        days = no_of_days or random.randint(5, 20)
        base_date = datetime.now().date()

        itineraries = []
        for day in range(days):
            start_time = datetime.combine(
                base_date + timedelta(days=day),
                time(hour=random.randint(9, 12), minute=random.choice([0, 15, 30, 45])),
            )
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            itineraries.append(
                {
                    "title": f"Day {day + 1}",
                    "description": fake.sentence(),
                    "location": self.get_location("TRIP_LOCATIONS"),
                    "category": self.get_category(),
                    "start_time": timezone.make_aware(start_time),
                    "end_time": timezone.make_aware(end_time),
                }
            )
        return itineraries
