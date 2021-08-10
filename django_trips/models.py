import json
from datetime import datetime, timezone

import django_trips.managers as managers
from config_models.models import ConfigurationModel
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_trips.mixins import SlugMixin


class Host(SlugMixin, models.Model):
    """
    Trip host model.

    This model contains the information for the trip hosts who are organizing
    trips.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cancellation_policy = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['name', 'verified']

    def __str__(self):
        """String representation of model instance"""
        return self.name


class Location(SlugMixin, models.Model):
    """
    Trip location model

    This model contains information about trip location with respect to
    coordinates. We will use coordinates to draw google map.
    """
    active = managers.ActiveModelManager()
    objects = models.Manager()

    destinations = managers.TripDestinationManager()
    departures = managers.TripDepartureManager()
    available = managers.AvailableLocationManager()
    deleted = models.BooleanField(default=False)
    is_destination = models.BooleanField(default=False)
    is_departure = models.BooleanField(default=False)

    name = models.CharField(max_length=30)
    slug = models.SlugField(null=True, blank=True)
    coordinates = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String representation of model instance"""
        return f"{self.name}"

    @property
    def get_coordinates(self):
        """Returns lat/lng in list."""
        return self.coordinates.split(',')


class Facility(SlugMixin, models.Model):
    """
    Trip Facility model

    This model contains information all the available facilities that can be
    provided in a trip.
    """
    name = models.CharField(max_length=70)
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
    objects = models.Manager()
    active = managers.ActiveModelManager()

    name = models.CharField("Title", max_length=500)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    description = models.TextField()
    # meta includes tinyurl, poster
    _metadata = models.TextField(default='{}', null=True, blank=True)

    duration = models.SmallIntegerField(default=0, null=True, blank=True)
    age_limit = models.SmallIntegerField(default=0, null=True, blank=True)

    destination = models.ForeignKey(Location, related_name='trip_destination', on_delete=models.CASCADE)
    departure = models.ForeignKey(Location, related_name='trip_departure', on_delete=models.CASCADE)
    locations = models.ManyToManyField(Location, related_name="trip_locations")

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)
    facilities = models.ManyToManyField(Facility, related_name="trip_facilities")
    gear = models.TextField("Recommended Gear", null=True, blank=True)

    deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'auth.User', related_name="created_by_trips", on_delete=models.CASCADE
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
        super().save(*args, **kwargs)
        self.slug = slugify(self.name)

    def get_absolute_url(self):
        return reverse('view_trip', {'slug': self.slug})

    @property
    def metadata(self):
        """Parse the internal metadata field into python object"""
        return json.loads(self._metadata)

    @property
    def cancellation_policy(self):
        """
        Trip's cancellation policy should be given preference over the
        generic host cancellation (all-host-trips) policy.
        """
        return self.host.cancellation_policy or CancellationPolicy.current().description


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
    price = models.SmallIntegerField(default=0)
    date_from = models.DateTimeField()

    def __str__(self):
        """String representation of model instance"""
        return self.trip.name

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
    schedule = models.ForeignKey(TripSchedule, related_name="trip_bookings", on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=30)
    cnic_number = models.CharField(max_length=30)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.name


class TripPickupLocation(models.Model):
    """Trip pickup locations"""
    trip = models.ForeignKey(TripSchedule, related_name="trip_pickup_locations", on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    additional_price = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.location
