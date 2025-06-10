"""Core data models for the app."""

import random

# pylint:disable=consider-using-from-import,missing-class-docstring,missing-function-docstring,no-member
from datetime import datetime
from datetime import timedelta

from config_models.models import ConfigurationModel
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import now
from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel
from taggit.managers import TaggableManager

import django_trips.managers as managers
from django_trips.choices import (
    AvailabilityType,
    BookingStatus,
    LocationType,
    ScheduleStatus,
    TripOptions,
)
from django_trips.mixins import SlugMixin

User = get_user_model()


class HostType(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<HostType: {self.name} slug: {self.slug}>"


class Host(SlugMixin, models.Model):
    """
    Trip host model.

    This model contains the information for the trip hosts who are organizing
    trips.
    """

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, unique=True, null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    type = models.ForeignKey(
        HostType,
        null=True,
        blank=True,
        related_name="hosts",
        on_delete=models.CASCADE,
    )
    cnic = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    cancellation_policy = models.JSONField(default=list, blank=True, null=True)
    refund_policy = models.JSONField(default=list, blank=True, null=True)

    verified = models.BooleanField(default=False)

    objects = managers.HostManager.as_manager()

    class Meta:
        ordering = ["name", "verified"]

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Host: {self.name} slug: {self.slug}>"


class HostRating(models.Model):
    host = models.OneToOneField(
        Host,
        related_name="ratings",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    rating_count = models.SmallIntegerField(default=0, null=True, blank=True)  # 32767
    rated_by = models.SmallIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f"{self.host}: {self.rating_count} / {self.rated_by}"

    def __repr__(self):
        return f"<HostRating: {self.rating_count} / {self.rated_by}"

    @property
    def average_rating(self):
        """Returns calculated rating."""
        return float(self.rating_count / self.rated_by) if self.rated_by else 0


class Location(SlugMixin, models.Model):
    """
    Represents a geographical location for trip locations.
    """

    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True, null=True, blank=True)

    travel_tips = models.JSONField(
        default=dict,
        help_text="Structured travel advice containing sections like 'transport', 'safety', etc.",
    )
    lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Latitude coordinate in decimal degrees (WGS84)",
    )
    lon = models.FloatField(
        null=True,
        blank=True,
        help_text="Longitude coordinate in decimal degrees (WGS84)",
    )
    type = models.CharField(
        max_length=100,
        choices=LocationType.choices,
        default=LocationType.TOWN,
        help_text="Classification of location type",
    )
    importance = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numerical importance ranking (higher = more significant)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this location should be shown publicly",
    )

    objects = managers.LocationQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name = "Trip Location"
        verbose_name_plural = "Trip Locations"

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Location: {self.name} slug: {self.slug}>"

    @property
    def coordinates(self):
        """Returns lat/lng in list."""
        return [self.lat, self.lon]


class Gear(SlugMixin, models.Model):
    """
    Gear options for a trip.

    This model contains information all the gears that can be used for a trip.
    """

    name = models.CharField(max_length=70, unique=True)
    slug = models.SlugField(max_length=85, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = managers.ActiveQuerySet.as_manager()

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Gear: {self.name} slug: {self.slug}>"


class Facility(SlugMixin, models.Model):
    """
    Trip Facility model

    This model contains information all the available facilities that can be
    provided in a trip.
    """

    name = models.CharField(max_length=70, unique=True)
    slug = models.SlugField(max_length=85, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = managers.ActiveQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Facilities"

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Facility: {self.name} slug: {self.slug}>"


class Category(SlugMixin, models.Model):
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=85, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = managers.ActiveQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Category: {self.name} slug: {self.slug}>"


class Trip(SlugMixin, models.Model):
    """
    Trip model

    This model contains the main information that will be presented to
    end users.
    """

    name = models.CharField("Title", max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed trip description (html supported).",
    )
    overview = models.TextField(
        blank=True,
        null=True,
        help_text="Short summary displayed in listings (plain text)",
    )
    included = models.TextField(
        blank=True, null=True, help_text="Bullet points of included services/features"
    )
    excluded = models.TextField(
        blank=True, null=True, help_text="Bullet points of excluded services/features"
    )
    add_ons = models.TextField(
        "Additional Information",
        blank=True,
        null=True,
        help_text="Optional upgrades or special offers",
    )
    travel_tips = models.JSONField(
        default=dict,
        help_text="Tips for travelers on this trip, structured as {'section_title': 'content',}",
    )
    requirements = models.JSONField(
        default=dict,
        help_text="User requirements on this trip, Example: {'fitness_level': 'moderate'}",
    )
    child_policy = models.JSONField(default=dict, help_text="Child policy on this trip")
    facilities = models.ManyToManyField(
        Facility, related_name="trips", help_text="Amenities available during the trip"
    )
    gear = models.ManyToManyField(
        Gear,
        related_name="trips",
        help_text="Equipment provided or required during the trip.",
    )

    # duration=timedelta(days=5)
    # trip.duration.days
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Format: DD HH:MM:SS (e.g., '5 00:00:00' for 5 days)",
    )
    passenger_limit_min = models.PositiveIntegerField(
        default=0, null=True, blank=True, help_text="0 means no minimum requirement"
    )
    passenger_limit_max = models.PositiveIntegerField(
        default=0, null=True, blank=True, help_text="0 means no maximum limit"
    )
    age_limit = models.SmallIntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Minimum age requirement (0 = no restriction)",
    )

    departure = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name="departure_trips",
        on_delete=models.CASCADE,
        help_text="Starting point of the trip",
    )
    destination = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name="destination_trips",
        on_delete=models.CASCADE,
        help_text="Primary destination of the trip",
    )
    locations = models.ManyToManyField(
        Location,
        related_name="trips",
        help_text="All locations visited during the trip",
    )
    country = CountryField(
        default="PK", db_index=True, help_text="Primary country where trip operates"
    )

    categories = models.ManyToManyField(
        Category,
        related_name="trips",
        help_text="Classification tags (e.g., 'Adventure', 'Family')",
    )

    # meta includes tinyurl, poster
    metadata = models.JSONField(default=dict, blank=True)

    is_featured = models.BooleanField(
        default=False, help_text="Display in featured/promoted sections"
    )
    is_pax_required = models.BooleanField(
        default=True, help_text="Whether passenger count must be specified"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="trips", on_delete=models.CASCADE)

    host = models.ForeignKey(
        Host,
        related_name="trips",
        on_delete=models.CASCADE,
        help_text="Organization/guide responsible for the trip",
    )

    tags = TaggableManager(help_text="Comma-separated tags for search/filtering")
    objects = managers.TripQuerySet.as_manager()

    def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.name}-by-{self.host}-for-{self.destination}")
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Trip: {self.name}, {self.departure} > {self.destination}>"

    @property
    def passenger_limit(self):
        return self.passenger_limit_min if self.passenger_limit_min is not None else 0

    @property
    def primary_category(self):
        return self.categories.first()

    @property
    def poster(self):
        return ""

    def get_absolute_url(self):
        return reverse("trips-api:trip-detail", kwargs={"identifier": self.slug})

    @property
    def cancellation_policy(self):
        """
        Trip's cancellation policy should be given preference over the
        generic host cancellation (all-host-trips) policy.
        """
        return self.host.cancellation_policy or CancellationPolicy.current().description

    @property
    def refund_policy(self):
        """
        Trip's cancellation policy should be given preference over the
        generic host cancellation (all-host-trips) policy.
        """
        return self.host.refund_policy or RefundPolicy.current().description

    def create_schedules(self):
        """
        Generates individual trip schedules based on the availability configuration.

        Flow Overview:
        -----------------
            Trip
             └── TripAvailability (type = DAILY, WEEKLY, etc.)
                   └── options = {
                           "date_from": <timestamp>,
                           "end_date": <timestamp>,
                           "is_per_person_price": <bool>
                       }
                   └── price
                   └── available_seats
                       └── create TripSchedule entries for each available date

        Example Structure:
        ------------------
            Trip: "3-Day Hunza Adventure"
                └── TripAvailability:
                        type: DAILY
                        price: 15000
                        options: {
                            "date_from": 01-May-2025,
                            "end_date": 20-May-2025,
                            "is_per_person_price": True
                        }
                        available_seats: 12

                        → create TripSchedules:
                            - 01 May 2025
                            - 02 May 2025
                            - 03 May 2025
                            - ...
                            - 20 May 2025

        Purpose:
        --------
        To pre-fill trip slots for booking on a per-day basis, based on configured
        availability rules. This allows end-users to see specific departure dates
        and book accordingly.

        Returns:
            int: Number of TripSchedule objects created
        """

        availability = self.trip_availability

        if not availability or availability.type != AvailabilityType.DAILY:
            return 0

        options = availability.options or {}
        required_keys = {"date_from", "end_date", "is_per_person_price"}
        if not required_keys.issubset(options):  # Required options are missing
            return 0

        try:
            schedule_start = datetime.fromtimestamp(
                options["date_from"] / 1000.0, tz=timezone.utc
            )
            schedule_end = datetime.fromtimestamp(
                options["end_date"] / 1000.0, tz=timezone.utc
            )
        except Exception:  # pylint:disable=broad-exception-caught
            return 0

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # We are not within the scheduling window
        if not schedule_start <= today <= schedule_end:
            return 0

        days_to_generate = min((schedule_end - today).days, 20)
        total_created = 0

        with transaction.atomic():
            for day_offset in range(days_to_generate):
                schedule_date = today + timedelta(days=day_offset)

                _, created = TripSchedule.objects.get_or_create(
                    trip=self,
                    date_from=schedule_date,
                    is_per_person_price=options["is_per_person_price"],
                    defaults={
                        "price": availability.price,
                        "available_seats": availability.available_seats,
                        "booked_seats": 0,
                    },
                )
                if created:
                    total_created += 1

        return total_created


class TripItinerary(models.Model):
    """
    Represents a day-wise plan or schedule of activities for a Trip.

    Used to describe what happens on each day of a multi-day trip. It can
    include details such as title, description, time slots, location, and
    category (e.g., hiking, sightseeing).
    """

    trip = models.ForeignKey(
        Trip, related_name="itinerary_days", on_delete=models.CASCADE
    )
    day_index = models.SmallIntegerField(default=1)
    title = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(default="")
    location = models.ForeignKey(
        Location, related_name="+", null=True, blank=True, on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category, related_name="+", null=True, blank=True, on_delete=models.CASCADE
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Day:{self.day_index}-{self.trip.name}"

    def __repr__(self):
        return f"<TripItinerary Day:{self.day_index}-{self.trip.name}"

    @property
    def duration(self) -> timedelta:
        """Returns the duration of the itinerary as a timedelta object."""
        return self.end_time - self.start_time

    class Meta:
        ordering = ["trip", "day_index"]
        verbose_name_plural = "Trip Itineraries"
        unique_together = ("trip", "day_index")


class TripAvailability(models.Model):
    """
    Represents the general availability window of a Trip.

    This model defines a time range (start to end date) during which a trip
    is available. It can be configured as DAILY, WEEKLY, FIXED, etc., using
    the `type` field.

    Each availability can include pricing and seating capacity, and is used
    to auto-generate specific `TripSchedule` entries for booking purposes.

    Use Case:
        - Used by `Trip.create_schedules()` to generate multiple TripSchedule
          entries within the defined availability window.
    """

    trip = models.ForeignKey(
        Trip,
        related_name="availabilities",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    price = models.DecimalField(default=0, max_digits=7, decimal_places=0)
    is_per_person_price = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    available_seats = models.PositiveSmallIntegerField(default=0)

    type = models.CharField(
        max_length=100,
        choices=AvailabilityType.choices,
        default=AvailabilityType.MONTHLY,
    )

    options = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Trip Availabilities"
        ordering = ["end_date", "price"]
        unique_together = ("trip", "start_date", "end_date")

    def __str__(self):
        return f"type:{self.type} - price:{self.price} - end_date: {self.start_date}"

    @property
    def is_active(self):
        if self.start_date and self.end_date:
            return self.start_date <= now() < self.end_date
        return False


class TripSchedule(models.Model):
    """
    Represents a specific scheduled instance of a Trip on a particular date.

    This model allows trips to be booked on specific dates with defined
    pricing and seat availability. It is generated automatically using the
    parent Trip's `TripAvailability` or can be manually created.

    Use Case:
        - Shown to end users as actual bookable trip dates.
        - Supports querying/filtering by date or availability.
    """

    trip = models.ForeignKey(Trip, related_name="schedules", on_delete=models.CASCADE)
    price = models.DecimalField(default=0, max_digits=7, decimal_places=0)
    is_per_person_price = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    available_seats = models.PositiveSmallIntegerField(default=0)
    booked_seats = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.DRAFT,
    )
    objects = managers.TripScheduleQuerySet.as_manager()

    def __str__(self):
        return f"{self.trip} - {self.start_date if self.start_date else 'N/A'}"

    def __repr__(self):
        return f"<TripSchedule host={self.start_date} trip={self.trip}>"

    @property
    def is_active(self):
        if self.start_date and self.end_date:
            return self.start_date <= now() < self.end_date
        return False


class TripOption(models.Model):
    """
    Represents optional configurations or tiers for a Trip.

    A trip can have multiple pricing tiers or styles (e.g., Standard, Deluxe,
    VIP), each with its own pricing and description. These options are linked
    directly to the Trip, not to specific schedules.

    Use Case:
    - Shown to users during booking to choose from trip tiers.
    - Helps support multiple pricing models under the same trip.
    """

    trip = models.ForeignKey(Trip, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(
        max_length=20,
        choices=TripOptions.choices,
        default=TripOptions.STANDARD,
    )

    description = models.TextField()
    base_price = models.DecimalField(default=0, max_digits=7, decimal_places=0)
    base_child_price = models.DecimalField(default=0, max_digits=7, decimal_places=0)

    class Meta:
        ordering = ["trip", "name"]
        unique_together = ("trip", "name")

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<TripOption {self.name}>"


class TripReview(models.Model):
    """Trip Review Model"""

    trip = models.ForeignKey(Trip, related_name="reviews", on_delete=models.CASCADE)
    meals = models.SmallIntegerField(default=0)
    accommodation = models.SmallIntegerField(default=0)
    transport = models.SmallIntegerField(default=0)
    value_for_money = models.SmallIntegerField(default=0)
    overall = models.SmallIntegerField(default=0)
    comment = models.TextField()
    # User details
    name = models.CharField(max_length=50)
    email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}-{self.overall}"

    def __repr__(self):
        return f"<TripReview {self.name}-{self.overall}"


class TripReviewSummary(models.Model):
    """Trip Review Summary Model"""

    trip = models.OneToOneField(
        Trip,
        related_name="review_summary",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meals = models.FloatField(default=0)
    accommodation = models.FloatField(default=0)
    transport = models.FloatField(default=0)
    value_for_money = models.FloatField(default=0)
    overall = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Trip review summaries"

    def __str__(self):
        return f"{self.trip}-{self.meals}-{self.accommodation}"

    def __repr__(self):
        return f"<TripReviewSummary trip={self.trip}-{self.meals}-{self.accommodation}"


class CancellationPolicy(ConfigurationModel):
    description = models.TextField()

    def __str__(self):
        return str(self.description)

    def __repr__(self):
        return f"<CancellationPolicy description={self.description}>"


class RefundPolicy(ConfigurationModel):
    description = models.TextField()

    def __str__(self):
        return str(self.description)

    def __repr__(self):
        return f"<CancellationPolicy description={self.description}>"


class TripBooking(TimeStampedModel):
    schedule = models.ForeignKey(
        TripSchedule, related_name="bookings", on_delete=models.CASCADE
    )
    number = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        help_text="Auto-generated booking reference number",
    )

    full_name = models.CharField(
        max_length=255, help_text="Full name of the primary contact person"
    )
    email = models.EmailField(
        help_text="Email address for booking confirmations and updates"
    )
    phone_number = models.CharField(
        max_length=30, help_text="Contact phone number with country code"
    )
    # pylint:disable=fixme
    # TODO: change this to adults/children/infants
    number_of_persons = models.PositiveIntegerField(
        default=1,
        help_text="Total number of participants",
    )
    target_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Preferred date/time for the trip.",
    )

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        help_text="Current status of the booking",
    )
    message = models.TextField(
        null=True, blank=True, help_text="Special requests or additional information"
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="bookings",
        on_delete=models.CASCADE,
        help_text="User who created this booking (null for guest bookings)",
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when booking was cancelled (null if active)",
    )
    objects = managers.TripBookingManager.as_manager()

    class Meta:
        verbose_name = "Trip Booking"
        verbose_name_plural = "Trip Bookings"
        ordering = ("target_date", "-created")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["schedule"]),
        ]

    def __str__(self):
        return f"<TripBooking {self.full_name}, {self.target_date}, {self.status}/>"

    def __repr__(self):
        return f"<TripBooking - {self.full_name}, {self.target_date}, {self.status}/>"

    def save(self, **kwargs):
        if not self.number:
            self.number = self.generate_booking_number()
        super().save(**kwargs)

    def cancel(self):
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save()
        return self

    def can_be_cancelled(self):
        return BookingStatus.can_be_cancelled(self.status)

    @classmethod
    def generate_booking_number(cls):
        """
        DPT00000107
        DPT00000284
        DPT00000332
        """
        prefix = "DPT"
        count = cls.objects.count() + 1
        padded_number = f"{count:06d}"  # e.g., 000123

        # Generate 2 random digits
        suffix = f"{random.randint(0, 99):02d}"

        return f"{prefix}{padded_number}{suffix}"


class TripPickupLocation(models.Model):
    """Trip pickup locations"""

    trip = models.ForeignKey(
        TripSchedule, related_name="pickup_locations", on_delete=models.CASCADE
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    additional_price = models.SmallIntegerField(default=0)

    def __str__(self):
        return str(self.location)

    def __repr__(self):
        return f"<TripPickupLocation trip={self.trip}-{self.location}>"
