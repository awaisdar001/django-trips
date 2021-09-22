"""Django Trips serializers"""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django_trips.models import (Category, Facility, Host, Location, Trip,
                                 TripItinerary, TripSchedule, TripBooking, Gear, TripAvailability)


class TripScheduleField(serializers.Field):
    """
    Trip schedule field.
    """

    def to_representation(self, value):
        breakpoint()
        ret = {
            "trip_id": value.trip.slug,
            "date": value.date_from,
            "price": value.price,
        }
        return ret

    def to_internal_value(self, data):
        breakpoint()
        ret = {
            "x_coordinate": data["x"],
            "y_coordinate": data["y"],
        }
        return ret


class UserSerializer(serializers.ModelSerializer):
    """User Modal Serializer"""
    full_name = serializers.CharField(source='get_full_name')

    class Meta:
        model = User
        fields = [
            'username',
            'full_name',
            'first_name',
            'last_name',
        ]


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class LocationSerializer(serializers.ModelSerializer):
    """Location Modal Serializer"""

    class Meta:
        model = Location
        fields = ('name', 'slug', 'coordinates')


class FacilitySerializer(serializers.ModelSerializer):
    """Facility Modal Serializer"""

    class Meta:
        model = Facility
        exclude = ('id', 'deleted',)


class GearSerializer(serializers.ModelSerializer):
    """Gear Modal Serializer"""

    class Meta:
        model = Gear
        exclude = ('id', 'deleted',)


class HostSerializer(serializers.ModelSerializer):
    """Host Modal Serializer"""
    type = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Host
        fields = ('name', 'slug', 'description', 'cancellation_policy', 'verified', 'type', 'rating')

    def get_type(self, object):
        return object.type.name

    def get_rating(self, object):
        rating = {
            'rating_count': 0,
            'rated_by': 0
        }
        host_rating = getattr(object, 'host_rating')
        if host_rating:
            rating['rating_count'] = host_rating.rating_count
            rating['rated_by'] = host_rating.rated_by
        return rating


class TripItinerarySerializer(serializers.ModelSerializer):
    """TripItinerary Modal Serializer"""

    class Meta:
        model = TripItinerary
        exclude = ('trip', 'id')


class TripAvailabilitySerializer(serializers.ModelSerializer):
    """TripItinerary Modal Serializer"""
    type = serializers.CharField(source='get_type_display')
    date_to = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = TripAvailability
        fields = ('type', 'price', 'date_to', 'options', 'is_per_person_price')


class TripScheduleSerializer(serializers.ModelSerializer):
    """TripSchedule Modal Serializer"""
    date_from = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = TripSchedule
        exclude = ('trip',)


class TripLightWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ('name', 'slug')


class TripSerializerWithIDs(serializers.ModelSerializer):
    class Meta:
        model = Trip
        exclude = ('_metadata',)

    def create(self, validated_data):
        return super(TripSerializerWithIDs, self).create(validated_data)


class TripBaseSerializer(serializers.ModelSerializer):
    trip_url = serializers.SerializerMethodField()
    starting_location = LocationSerializer()
    destination = LocationSerializer()
    created_by = UserSerializer(read_only=True)
    trip_schedule = serializers.SerializerMethodField()
    trip_itinerary = TripItinerarySerializer(many=True)
    trip_availability = TripAvailabilitySerializer()
    locations = LocationSerializer(many=True)
    facilities = FacilitySerializer(many=True)
    gear = GearSerializer(many=True)
    primary_category = CategorySerializer()
    categories = CategorySerializer(many=True)

    class Meta:
        fields = (
            'name',
            'slug',
            'trip_url',
            'description',
            'duration',
            'age_limit',
            'starting_location',
            'destination',
            'primary_category',
            'categories',
            'gear',
            'metadata',
            'locations',
            'trip_schedule',
            'trip_itinerary',
            'trip_availability',
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
    host = HostSerializer(read_only=True)

    class Meta:
        model = TripBaseSerializer.Meta.model
        fields = TripBaseSerializer.Meta.fields + ('cancellation_policy', 'host')


class DestinationMinimumSerializer(serializers.ModelSerializer):
    destination_url = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ('slug', 'name', 'destination_url')

    def get_destination_url(self, destination):
        return reverse("trips-api:destination-item", kwargs={"slug": destination.slug})


class TripBookingSerializer(serializers.ModelSerializer):
    trip = TripLightWeightSerializer()
    target_date = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = TripBooking
        exclude = ()


class TripBookingCreateSerializer(serializers.ModelSerializer):
    trip = TripLightWeightSerializer()
    target_date = serializers.DateTimeField(format="%Y-%m-%d")

    def to_internal_value(self, data):
        if 'trip' in data:
            data['trip'] = Trip.objects.filter(slug=data['trip']).first()
        return data

    def validate(self, attrs):
        if not isinstance(attrs.get('trip'), Trip):
            raise ValidationError({'trip': {'detail': 'Trip not found', 'code': 400}})
        return attrs

    class Meta:
        model = TripBookingSerializer.Meta.model
        exclude = ()
