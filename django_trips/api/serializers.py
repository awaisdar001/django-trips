from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import serializers

from trips.models import (
    Facility, Host, Location, Trip, TripItinerary, TripSchedule,
)


class UserSerializer(serializers.ModelSerializer):
    """User Modal Serializer"""

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff')


class LocationSerializer(serializers.ModelSerializer):
    """Location Modal Serializer"""

    class Meta:
        model = Location
        fields = '__all__'


class FacilitySerializer(serializers.ModelSerializer):
    """Facility Modal Serializer"""

    class Meta:
        model = Facility
        fields = '__all__'


class HostSerializer(serializers.ModelSerializer):
    """Host Modal Serializer"""

    class Meta:
        model = Host
        fields = '__all__'


class TripItinerarySerializer(serializers.ModelSerializer):
    """TripItinerary Modal Serializer"""

    class Meta:
        model = TripItinerary
        fields = '__all__'


class TripScheduleSerializer(serializers.ModelSerializer):
    """TripSchedule Modal Serializer"""

    class Meta:
        model = TripSchedule
        exclude = ('trip',)


class TripBaseSerializer(serializers.ModelSerializer):
    trip_url = serializers.SerializerMethodField()
    metadata = serializers.JSONField()
    destination = LocationSerializer()
    created_by = UserSerializer(read_only=True)
    trip_schedule = serializers.SerializerMethodField()
    trip_itinerary = TripItinerarySerializer(many=True)
    locations = LocationSerializer(many=True)
    facilities = FacilitySerializer(many=True)

    class Meta:
        fields = (
            'name', 'slug', 'description', 'duration', 'age_limit', 'destination',
            'metadata', 'category', 'gear', 'created_by', 'trip_schedule',
            'trip_itinerary', 'locations', 'facilities'
        )
        model = Trip

    def get_trip_url(self, trip):
        return reverse('trips-detail', kwargs={'pk': trip.id})

    def get_trip_schedule(self, trip):
        qs = TripSchedule.available.filter(trip=trip)
        serializer = TripScheduleSerializer(instance=qs, many=True)
        return serializer.data


class TripDetailSerializer(TripBaseSerializer):
    """
    Trip Detail Modal Serializer

    This Serializer is used for trip object retrieval as it requires all
    the details of the object
    """
    cancellation_policy = serializers.CharField(read_only=True)
    host = HostSerializer(read_only=True)

    def get_cancellation_policy(self, trip):
        return trip.cancellation_policy

    class Meta:
        model = Trip
        fields = TripBaseSerializer.Meta.fields + ('cancellation_policy', 'host')


class TripListSerializer(TripBaseSerializer):
    """
    Trip List Modal Serializer

    This Serializer is used for the trips listing as it requires
    minimal information
    """
    pass
