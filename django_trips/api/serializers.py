"""Django Trips serializers"""
from django.contrib.auth.models import User
from django.urls import reverse
from django_trips.models import (Category, Facility, Host, Location, Trip,
                                 TripItinerary, TripSchedule)
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """User Modal Serializer"""

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff')


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""

    class Meta:
        model = Category
        fields = '__all__'


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
        fields = "__all__"


class TripScheduleSerializer(serializers.ModelSerializer):
    """TripSchedule Modal Serializer"""

    class Meta:
        model = TripSchedule
        exclude = ('trip',)


class TripSerializerWithIDs(serializers.ModelSerializer):
    class Meta:
        model = Trip
        exclude = ('_metadata',)

    def create(self, validated_data):
        return super(TripSerializerWithIDs, self).create(validated_data)


class TripBaseSerializer(serializers.ModelSerializer):
    trip_url = serializers.SerializerMethodField()
    metadata = serializers.JSONField(source="_metadata", initial="{}")
    departure = LocationSerializer()
    destination = LocationSerializer()
    created_by = UserSerializer(read_only=True)
    trip_schedule = serializers.SerializerMethodField()
    trip_itinerary = TripItinerarySerializer(many=True)
    locations = LocationSerializer(many=True)
    facilities = FacilitySerializer(many=True)
    category = CategorySerializer()

    class Meta:
        fields = (
            'name',
            'slug',
            'trip_url',
            'description',
            'duration',
            'age_limit',
            'departure',
            'destination',
            'category',
            'gear',
            'metadata',
            'locations',
            'trip_schedule',
            'trip_itinerary',
            'facilities',
            'created_by',
        )
        model = Trip

    def get_trip_url(self, trip):
        return reverse("trips-api:trip-item-slug", kwargs={"slug": trip.slug})

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


class DestinationMinimumSerializer(serializers.ModelSerializer):
    destination_url = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ('slug', 'name', 'destination_url')

    def get_destination_url(self, destination):
        return reverse("trips-api:destination-item", kwargs={"slug": destination.slug})
