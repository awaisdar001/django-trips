import random
import traceback
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from django_trips.choices import LocationType, ScheduleStatus, TripOptions
from django_trips.models import (
    Category,
    Facility,
    Gear,
    Host,
    HostType,
    Location,
    Trip,
    TripItinerary,
    TripOption,
    TripReview,
    TripReviewSummary,
    TripSchedule,
)

fake = Faker()
User = get_user_model()

DEFAULT_SETTINGS = {
    "TRIP_DESTINATIONS": ["Boston", "London"],
    "TRIP_DEPARTURE_LOCATION": ["Boston"],
    "TRIP_LOCATIONS": ["Boston", "London", "Delhi"],
    "TRIP_LOCATIONS_BY_REGION": {"Test Region": ["Boston", "London", "Delhi"]},
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
                self.create_reviews(trip)
                self.stdout.write(
                    self.style.SUCCESS(f"Trip Created: <id={trip.pk} name={trip.name}>")
                )
            except Exception as e:  # pylint:disable=broad-except
                self.stderr.write(traceback.format_exc())
                raise CommandError(f"Error creating trip: {e}") from e

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
            metadata={
                "poster": fake.image_url(width=640, height=480),
                "tinyurl": fake.url(),
            },
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

    def create_reviews(self, trip):
        """
        Create a handful of reviews for the trip, then a TripReviewSummary
        averaging the *verified* ones - matching how the public API only
        counts verified reviews (see TripListSerializer/TripDetailSerializer's
        review_summary field).
        """
        for _ in range(random.randint(3, 15)):
            TripReview.objects.create(
                trip=trip,
                meals=random.randint(1, 5),
                accommodation=random.randint(1, 5),
                transport=random.randint(1, 5),
                value_for_money=random.randint(1, 5),
                overall=random.randint(1, 5),
                comment=fake.paragraph(nb_sentences=2),
                name=fake.name(),
                email=fake.email(),
                is_verified=random.random() < 0.8,
            )

        verified_reviews = trip.reviews.filter(is_verified=True)
        if not verified_reviews.exists():
            return None

        averages = verified_reviews.aggregate(
            meals=Avg("meals"),
            accommodation=Avg("accommodation"),
            transport=Avg("transport"),
            value_for_money=Avg("value_for_money"),
            overall=Avg("overall"),
        )
        return TripReviewSummary.objects.update_or_create(
            trip=trip, defaults=averages
        )[0]

    def get_location(self, key):
        name = random.choice(self.get_setting(key))
        return self.get_or_create_location(name)

    def get_locations(self):
        names = random.sample(self.get_setting("TRIP_LOCATIONS"), random.randint(1, 3))
        return [self.get_or_create_location(name) for name in names]

    def get_or_create_location(self, name):
        """
        Get-or-create a Location by name, backfilling its region's
        PROVINCE-level parent per TRIP_LOCATIONS_BY_REGION whenever it isn't
        already linked - not just on first creation, so re-running this
        command against a DB with pre-existing (e.g. previously seeded
        before this mapping existed) Location rows still fixes them up
        instead of leaving `region` as None forever.
        """
        location, _ = Location.objects.get_or_create(
            slug=slugify(name), defaults={"name": name}
        )
        if not location.parent_id:
            region_name = self.get_region_for_location(name)
            if region_name:
                location.parent = self.get_or_create_region(region_name)
                location.save(update_fields=["parent"])
        return location

    def get_region_for_location(self, name):
        """Return the region name `name` belongs to per
        TRIP_LOCATIONS_BY_REGION, or None if it isn't mapped to one."""
        regions = self.get_setting("TRIP_LOCATIONS_BY_REGION")
        for region_name, location_names in regions.items():
            if name in location_names:
                return region_name
        return None

    def get_or_create_region(self, region_name):
        return Location.objects.get_or_create(
            slug=slugify(region_name),
            defaults={"name": region_name, "type": LocationType.PROVINCE},
        )[0]

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
            name=name, defaults={"verified": True, "type": host_type}
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
