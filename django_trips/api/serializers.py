from django.contrib.auth.models import User
from rest_framework import serializers

from trips.models import (
    Facility, Host, Location, Trip, TripItinerary, TripSchedule,
)


class UserSerializer(serializers.ModelSerializer):
    """User Modal Serializer"""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')


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
        fields = '__all__'


class TripDetailSerializer(serializers.ModelSerializer):
    """
    Trip Detail Modal Serializer

    This Serializer is used for trip object retrieval as it requires all
    the details of the object
    """
    trip_schedule = serializers.SerializerMethodField()
    trip_itinerary = TripItinerarySerializer(many=True)

    cancellation_policy = serializers.CharField(read_only=True)
    metadata = serializers.JSONField()
    facilities = FacilitySerializer(many=True)
    starting_location = LocationSerializer()
    locations = LocationSerializer(many=True)
    host = HostSerializer()
    created_by = UserSerializer()

    def get_trip_schedule(self, trip):
        qs = TripSchedule.available.filter(trip=trip)
        serializer = TripScheduleSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        exclude = ('_cancellation_policy',)
        model = Trip


class TripListSerializer(serializers.ModelSerializer):
    """
    Trip List Modal Serializer

    This Serializer is used for the trips listing as it requires
    minimal information
    """

    trip_schedule = serializers.SerializerMethodField()

    facilities = FacilitySerializer(many=True)
    starting_location = LocationSerializer()
    metadata = serializers.JSONField()
    locations = LocationSerializer(many=True)

    def get_trip_schedule(self, trip):
        qs = TripSchedule.available.filter(trip=trip)
        serializer = TripScheduleSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        exclude = (
            '_cancellation_policy', 'host', 'created_by', 'created_at', 'updated_at',
            'deleted', 'gear'
        )
        model = Trip
