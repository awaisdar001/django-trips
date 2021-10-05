import json
from datetime import datetime, timedelta

from config_models.models import ConfigurationModel
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from tagging.registry import register

import django_trips.managers as managers
from django_trips.mixins import SlugMixin


class HostType(models.Model):
    """Host type model."""
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String representation of model instance"""
        return self.name


class Host(SlugMixin, models.Model):
    """
    Trip host model.

    This model contains the information for the trip hosts who are organizing
    trips.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    type = models.ForeignKey(HostType, null=True, blank=True, related_name='host_type', on_delete=models.CASCADE)
    cnic = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=50, null=True, blank=True)
    _cancellation_policy = models.TextField(default='[]', null=True, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['name', 'verified']

    def __str__(self):
        """String representation of model instance"""
        return self.name

    @property
    def cancellation_policy(self):
        """Host cancellation policy."""
        return json.loads(self._cancellation_policy)

    @cancellation_policy.setter
    def cancellation_policy(self, value):
        self._cancellation_policy = json.dumps(value)


class HostRating(models.Model):
    host = models.OneToOneField(
        Host, related_name="host_rating", on_delete=models.CASCADE, null=True, blank=True
    )
    rating_count = models.SmallIntegerField(default=0, null=True, blank=True)  # 32767
    rated_by = models.SmallIntegerField(default=0, null=True, blank=True)

    @property
    def average_rating(self):
        """Returns calculated rating."""
        return float(self.rating_count / self.rated_by) if self.rated_by else 0

    def __str__(self):
        """String representation of model instance"""
        return f'{self.host.name}: {self.rating_count} / {self.rated_by}'


class Location(SlugMixin, models.Model):
    """
    Trip location model

    This model contains information about trip location with respect to
    coordinates. We will use coordinates to draw google map.
    """
    TOWN = 'TW'
    CITY = 'CT'
    PROVINCE = 'PR'

    LOCATION_TYPE_CHOICES = [
        (TOWN, 'Town'),
        (CITY, 'City'),
        (PROVINCE, 'Province'),
    ]

    active = managers.ActiveModelManager()
    available = managers.LocationAvailableManager()
    objects = models.Manager()

    name = models.CharField(max_length=30)
    slug = models.SlugField(null=True, blank=True)
    coordinates = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=2, choices=LOCATION_TYPE_CHOICES, default=TOWN)
    importance = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="unique_slug_for_location", fields=("slug",), )
        ]
        ordering = ['name']

    def __str__(self):
        """String representation of model instance"""
        return f"{self.name}"

    @property
    def get_coordinates(self):
        """Returns lat/lng in list."""
        return self.coordinates.split(',')


class Gear(SlugMixin, models.Model):
    """
    Gear options for a trip.

    This model contains information all the gears that can be used for a trip.
    """
    name = models.CharField(max_length=70, unique=True)
    slug = models.SlugField(max_length=85, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Facility(SlugMixin, models.Model):
    """
    Trip Facility model

    This model contains information all the available facilities that can be
    provided in a trip.
    """
    name = models.CharField(max_length=70, unique=True)
    slug = models.SlugField(max_length=85, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Facilities'

    def __str__(self):
        """String representation of model instance"""
        return self.name


class Category(SlugMixin, models.Model):
    """Trip Category model"""
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=85, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Trip(SlugMixin, models.Model):
    """
    Trip model

    This model contains the main information that will be presented to
    end users.
    """
    STANDARD = 'ST'
    BUDGET = 'BG'
    PREMIUM = 'PM'
    PRICE_BRACKET_CHOICES = [
        (STANDARD, 'Standard'),
        (BUDGET, 'Budget'),
        (PREMIUM, 'Premium'),
    ]
    objects = models.Manager()
    active = managers.ActiveModelManager()

    name = models.CharField("Title", max_length=500)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    description = models.TextField()

    # meta includes tinyurl, poster
    _metadata = models.TextField(default='{}', null=True, blank=True)
    price_bracket = models.CharField(max_length=2, choices=PRICE_BRACKET_CHOICES, default=STANDARD, )
    duration = models.SmallIntegerField(default=0, null=True, blank=True)
    age_limit = models.SmallIntegerField(default=0, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    destination = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name='trip_destination',
        on_delete=models.CASCADE
    )
    starting_location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name='trip_starting_location',
        on_delete=models.CASCADE,
    )
    locations = models.ManyToManyField(Location, related_name="trip_locations")
    passenger_limit = models.SmallIntegerField(default=0, null=True, blank=True)
    primary_category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)

    categories = models.ManyToManyField(Category, related_name="trip_categories")
    facilities = models.ManyToManyField(Facility, related_name="trip_facilities")
    gear = models.ManyToManyField(Gear, related_name="trip_gear")

    deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'auth.User',
        related_name="created_by_trips",
        on_delete=models.CASCADE
    )
    host = models.ForeignKey(Host, related_name="host_trips", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of model instance"""
        return self.name

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        self.slug = slugify(f'{self.name}-by-{self.host.name}-from-{self.starting_location.name}')
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('view_trip', {'slug': self.slug})

    @property
    def metadata(self):
        """Parse the internal metadata field into python object"""
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        """Setter method for """
        self._metadata = json.dumps(value)

    @property
    def cancellation_policy(self):
        """
        Trip's cancellation policy should be given preference over the
        generic host cancellation (all-host-trips) policy.
        """
        return self.host.cancellation_policy or CancellationPolicy.current().description

    def create_schedules(self):
        """
        Creates schedules from the trip availability options.
        """
        from datetime import datetime

        from django.utils import timezone

        availability = self.trip_availability
        if not availability:
            return

        if availability.type == TripAvailability.DAILY:
            total_created = 0

            options = availability.options
            today = datetime.now(timezone.utc)
            schedule_from = datetime.fromtimestamp(options['date_from'] / 1000.0, tz=timezone.utc)
            schedule_to = datetime.fromtimestamp(options['date_to'] / 1000.0, tz=timezone.utc)
            if schedule_from < today < schedule_to:
                for day in range(20):
                    schedule_date = (today + timedelta(days=day))
                    instance, created = TripSchedule.objects.get_or_create(
                        trip=self,
                        date_from=schedule_date,
                        is_per_person_price=availability['is_per_person_price'],
                        defaults={
                            'price': availability.price,
                        }
                    )
                    if created:
                        total_created += 1
            return total_created
        return 0


class TripAvailability(models.Model):
    """Trip future availabilities"""
    DAILY = 'DL'
    WEEKLY = 'WK'
    MONTHLY = 'MN'
    FIX_DATE = 'FD'
    AVAILABILITY_CHOICES = [
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (FIX_DATE, 'FixDate'),
    ]
    trip = models.OneToOneField(Trip, null=True, blank=True, related_name='trip_availability', on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=AVAILABILITY_CHOICES, default=MONTHLY)
    date_to = models.DateTimeField()
    price = models.DecimalField(default=0, max_digits=7, decimal_places=0)
    is_per_person_price = models.BooleanField(default=True)
    _options = models.TextField(default='{}', null=True, blank=True)

    def __str__(self):
        return f'type:{self.type} - price:{self.price} - date_to: {self.date_to.date()}'

    class Meta:
        ordering = ['date_to', 'price']

    @property
    def options(self):
        return json.loads(self._options)

    @options.setter
    def options(self, value):
        self._options = json.dumps(value)


class TripItinerary(models.Model):
    """
    Trip itinerary model

    This model describes a trip with respect to each day.
    """
    trip = models.ForeignKey(Trip, related_name="trip_itinerary", on_delete=models.CASCADE)
    day = models.SmallIntegerField(default=0)
    heading = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(default='')

    def __str__(self):
        """String representation of model instance"""
        return "Day:{0}-{1}".format(self.day, self.trip.name)

    class Meta:
        ordering = ['trip', 'day']
        verbose_name_plural = 'Trip Itineraries'
        unique_together = ('trip', 'day',)


class TripSchedule(models.Model):
    """
    Trip schedule model

    This model contains information of upcoming trips
    """
    objects = models.Manager()
    available = managers.AvailableTripScheduleManager()

    trip = models.ForeignKey(Trip, related_name="trip_schedule", on_delete=models.CASCADE)
    price = models.DecimalField(default=0, max_digits=7, decimal_places=0)
    is_per_person_price = models.BooleanField(default=True)
    date_from = models.DateTimeField()

    def __str__(self):
        """String representation of model instance"""
        return f'{self.trip.host}: {self.trip.name} - {self.date_from.date()}'

    @property
    def is_active(self):
        return self.date_from <= datetime.now()


class TripReview(models.Model):
    """Trip Review Model"""
    trip = models.ForeignKey(Trip, related_name="trip_reviews", on_delete=models.CASCADE)
    meals = models.SmallIntegerField(default=0)
    accommodation = models.SmallIntegerField(default=0)
    transport = models.SmallIntegerField(default=0)
    value_for_money = models.SmallIntegerField(default=0)
    overall = models.SmallIntegerField(default=0)
    comment = models.TextField()
    #     User details
    name = models.CharField(max_length=50)
    email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    #     timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}-{}".format(self.name, self.overall)


class TripReviewSummary(models.Model):
    """Trip Review Summary Model"""
    trip = models.OneToOneField(
        Trip, related_name="trip_review_summary", on_delete=models.CASCADE, null=True, blank=True
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


class CancellationPolicy(ConfigurationModel):
    """CancellationPolicyModel model"""
    description = models.TextField()

    def __str__(self):
        return self.description


class TripBooking(models.Model):
    """Trip booking"""
    trip = models.ForeignKey(Trip, related_name="trip_bookings", null=True, blank=True, on_delete=models.CASCADE)
    target_date = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=30)
    cnic_number = models.CharField(max_length=30)
    email = models.EmailField()
    message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('target_date', '-created_at')

    def __str__(self):
        return f'<TripBooking {self.trip} - {self.name}, {self.target_date} />'


class TripPickupLocation(models.Model):
    """Trip pickup locations"""
    trip = models.ForeignKey(TripSchedule, related_name="trip_pickup_locations", on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    additional_price = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.location


# Register tags.
register(Trip)
