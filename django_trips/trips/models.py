import json

from django.db import models
from django.urls import reverse
from trips.managers import ActiveTripManager, AvailableTripScheduleManager


class Host(models.Model):
    """
    Trip host model.

    This model contains the information for the trip hosts who are organizing
    trips.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cancelation_policy = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['name', 'verified']

    def __str__(self):
        """String representation of model instance"""
        return "{0}".format(self.name)


class Location(models.Model):
    """
    Trip location model

    This model contains information about trip location with respect to
    coordinates. We will use coordinates to draw google map.
    """
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=50, null=True, blank=True)
    coordinates = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String representation of model instance"""
        return "{0}".format(self.name)


class Activity(models.Model):
    """
    Trip activity model

    This model contains what kind of activities a trip will offer.
    """
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Activities'

    def __str__(self):
        """String representation of model instance"""
        return "{0}".format(self.name)


class Facility(models.Model):
    """
    Trip Facility model

    This model contains information all the available facilities that can be
    provided in a trip.
    """
    name = models.CharField(max_length=70)
    slug = models.SlugField(max_length=85, null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Facilities'

    def __str__(self):
        """String representation of model instance"""
        return "{0}".format(self.name)


class Trip(models.Model):
    """
    Trip model

    This model contains the main information that will be presented to
    end users.
    """
    objects = models.Manager()
    active = ActiveTripManager()

    name = models.CharField("Title", max_length=500, null=True, blank=True)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    description = models.TextField("Description", null=True, blank=True)
    # meta includes tinyurl, poster
    _metadata = models.TextField(default='{}', null=True, blank=True)

    duration = models.SmallIntegerField(default=0, null=True, blank=True)
    price = models.SmallIntegerField(default=0, null=True, blank=True)
    starting_location = models.ForeignKey(
        Location, related_name="trip_starting_location", on_delete=models.CASCADE)

    locations_included = models.ManyToManyField(
        Location, related_name="trip_locations")
    activities = models.ManyToManyField(Activity)
    facilities = models.ManyToManyField(Facility)

    _cancelation_policy = models.TextField(
        "Cancelation Policy Override", null=True, blank=True)
    gear = models.TextField("Recommended Gear", null=True, blank=True)

    deleted = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        'auth.User', related_name="created_by_trips", on_delete=models.CASCADE)
    host = models.ForeignKey(Host, related_name="host_trips", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of model instance"""
        return u"{0} - {1}".format(self.name, self.host)

    class Meta:
        ordering = ['-created_at', '-id']

    
    def get_absolute_url(self):
        return reverse('view_trip', {'slug': self.slug})
        

    @property
    def metadata(self):
        """Parse the internal metadata field into python object"""
        return json.loads(self._metadata)

    @property
    def cancelation_policy(self):
        """
        Trip's cancelation policy should be given preference over the
        generic host cancelation (all-host-trips) policy.
        """
        return self._cancelation_policy or self.host.cancelation_policy


class TripItinerary(models.Model):
    """
    Trip itinerary model

    This model describes a trip with respect to each day.
    """
    trip = models.ForeignKey(Trip, related_name="trip_itinerary", on_delete=models.CASCADE)
    day = models.SmallIntegerField(default=0)
    description = models.TextField(default='')

    def __str__(self):
        """String representation of model instance"""
        return u"{0}-{1}".format(self.day, self.trip.name)

    class Meta:
        ordering = ['trip', 'day']
        verbose_name_plural = 'Trip Itineraries'


class TripSchedule(models.Model):
    """
    Trip schedule model

    This model contains information of upcoming trips
    """
    objects = models.Manager()
    available = AvailableTripScheduleManager()

    trip = models.ForeignKey(Trip, related_name="trip_schedule", on_delete=models.CASCADE)
    date_from = models.DateTimeField()
    price_override = models.SmallIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        """String representation of model instance"""
        return u"{0} - {1}".format(self.trip, self.date_from)
