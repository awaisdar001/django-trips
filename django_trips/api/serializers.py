"""Django Trips serializers"""

import crum
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from taggit.serializers import TagListSerializerField, TaggitSerializer

from django_trips.models import (
    Category,
    Facility,
    Gear,
    Host,
    Location,
    Trip,
    TripAvailability,
    TripBooking,
    TripItinerary,
    TripSchedule,
    TripOption,
)
from django_countries.serializer_fields import CountryField


class UserSerializer(serializers.ModelSerializer):
    """User Modal Serializer"""

    full_name = serializers.CharField(source="get_full_name")

    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "first_name",
            "last_name",
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")


class LocationSerializer(serializers.ModelSerializer):
    """Location Modal Serializer"""

    type = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            "name",
            "slug",
            "travel_tips",
            "lat",
            "lon",
            "type",
            "importance",
        )

    @extend_schema_field({"type": "string", "example": "TOWN"})
    def get_type(self, location):
        """Returns human readable model choice value."""
        return location.get_type_display()


class FacilitySerializer(serializers.ModelSerializer):
    """Facility Modal Serializer"""

    class Meta:
        model = Facility
        fields = ("id", "name", "slug", "is_active")


class GearSerializer(serializers.ModelSerializer):
    """Gear Modal Serializer"""

    class Meta:
        model = Gear
        fields = ("id", "name", "slug", "is_active")


class HostSerializer(serializers.ModelSerializer):
    """Host Modal Serializer"""

    type = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Host
        fields = (
            "name",
            "slug",
            "description",
            "cancellation_policy",
            "verified",
            "type",
            "rating",
        )

    @extend_schema_field({"type": "string", "example": "Tour Operator"})
    def get_type(self, host):
        return host.type.name if host else ""

    @extend_schema_field(
        {
            "type": "object",
            "properties": {
                "rating_count": {"type": "number"},
                "rated_by": {"type": "number"},
            },
        }
    )
    def get_rating(self, host):
        rating = {"rating_count": 0, "rated_by": 0}
        host_rating = getattr(host, "host_rating", None)
        if host_rating:
            rating["rating_count"] = host_rating.rating_count
            rating["rated_by"] = host_rating.rated_by
        return rating


class BaseTripItinerarySerializer(serializers.ModelSerializer):
    day = serializers.IntegerField(source="day_index")
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.active(), allow_null=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.active(), allow_null=True, required=False
    )

    class Meta:
        model = TripItinerary
        fields = (
            "day",
            "title",
            "description",
            "location",
            "category",
            "start_time",
            "end_time",
        )


class TripItineraryWriteSerializer(BaseTripItinerarySerializer):
    class Meta(BaseTripItinerarySerializer.Meta):
        fields = BaseTripItinerarySerializer.Meta.fields


class TripCreateSerializer(serializers.ModelSerializer):
    departure = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.active(),
        help_text="Primary location identifier where the trip starts.",
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.active(),
        help_text="Main destination identifier of the trip.",
    )
    host = serializers.PrimaryKeyRelatedField(
        queryset=Host.objects.active().all(),
        help_text="Tour operator or individual identifier hosting the trip.",
    )

    # ManyToMany fields
    trip_itinerary = TripItineraryWriteSerializer(
        many=True,
        required=False,
        allow_null=True,
        help_text="Day-wise breakdown of trip activities.",
    )
    locations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Location.objects.active(),
        help_text="All location identifiers covered during the trip.",
    )
    facilities = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Facility.objects.active(),
        help_text="Facilities identifiers included in the trip (e.g. transport, meals).",
    )
    gear = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Gear.objects.active(),
        help_text="Gear or equipment identifiers provided or required.",
    )
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.active(),
        help_text="Trip categories identifiers such as hiking or camping.",
    )
    tags = TagListSerializerField(
        help_text="Searchable tags for the trip (e.g. 'mountains', 'adventure')."
    )

    class Meta:
        model = Trip
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "overview",
            "included",
            "excluded",
            "add_ons",
            "travel_tips",
            "requirements",
            "child_policy",
            "facilities",
            "gear",
            "duration",
            "passenger_limit_min",
            "passenger_limit_max",
            "age_limit",
            "departure",
            "destination",
            "locations",
            "country",
            "categories",
            "is_featured",
            "is_pax_required",
            "is_active",
            "host",
            "tags",
            "trip_itinerary",
        )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("No data provided in the request body.")
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        user = crum.get_current_user()

        # Pop M2M fields
        itinerary_data = validated_data.pop("trip_itinerary", [])
        locations = validated_data.pop("locations", [])
        facilities = validated_data.pop("facilities", [])
        gear = validated_data.pop("gear", [])
        categories = validated_data.pop("categories", [])
        tags = validated_data.pop("tags", [])

        # Create trip instance
        trip = super().create(dict(**validated_data, created_by=user))

        # Add M2M relationships
        trip.locations.set(locations)
        trip.facilities.set(facilities)
        trip.gear.set(gear)
        trip.categories.set(categories)
        trip.tags.set(tags)

        for item in itinerary_data:
            TripItinerary.objects.create(trip=trip, **item)

        return trip

    @transaction.atomic
    def update(self, instance, validated_data):
        itinerary_data = validated_data.pop("trip_itinerary", None)
        locations = validated_data.pop("locations", None)
        facilities = validated_data.pop("facilities", None)
        gear = validated_data.pop("gear", None)
        categories = validated_data.pop("categories", None)
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if locations is not None:
            instance.locations.set(locations)
        if facilities is not None:
            instance.facilities.set(facilities)
        if gear is not None:
            instance.gear.set(gear)
        if categories is not None:
            instance.categories.set(categories)
        if tags is not None:
            instance.tags.set(tags)

        if itinerary_data is not None:
            # Simplest: clear all existing itineraries and create new ones
            instance.itinerary_days.all().delete()
            for item in itinerary_data:
                TripItinerary.objects.create(trip=instance, **item)

        return instance


class TripListSerializer(serializers.ModelSerializer):
    destination = LocationSerializer()
    duration = serializers.SerializerMethodField()
    trip_url = serializers.SerializerMethodField()
    country = CountryField()
    categories = CategorySerializer(many=True)
    host = HostSerializer()

    class Meta:
        model = Trip
        fields = (
            "name",
            "slug",
            "description",
            "destination",
            "duration",
            "country",
            "categories",
            "is_featured",
            "trip_url",
            "host",
        )

    @extend_schema_field({"type": "string", "example": "1 week 5 days"})
    def get_duration(self, obj):
        return str(obj.duration) if obj.duration else None

    @extend_schema_field(
        {"type": "string", "example": "api/v1/trips/2-days-trip-to-isb"}
    )
    def get_trip_url(self, trip):
        return reverse("trips-api:trip-detail", kwargs={"identifier": trip.slug})


class TripItineraryReadSerializer(BaseTripItinerarySerializer):
    location = LocationSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta(BaseTripItinerarySerializer.Meta):
        fields = BaseTripItinerarySerializer.Meta.fields


class TripOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripOption
        fields = ("name", "description", "base_price", "base_child_price")


class TripDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    cancellation_policy = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    trip_url = serializers.SerializerMethodField()
    facilities = FacilitySerializer(many=True)
    gear = GearSerializer(many=True)
    departure = LocationSerializer()
    destination = LocationSerializer()
    locations = LocationSerializer(many=True)
    country = CountryField()
    categories = CategorySerializer(many=True)
    created_by = UserSerializer(read_only=True)

    host = HostSerializer()
    tags = TagListSerializerField(required=False)
    trip_itinerary = TripItineraryReadSerializer(source="itinerary_days", many=True)
    options = TripOptionSerializer(many=True)

    class Meta:
        model = Trip
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "duration",
            "overview",
            "included",
            "excluded",
            "add_ons",
            "travel_tips",
            "requirements",
            "child_policy",
            "facilities",
            "gear",
            "duration",
            "passenger_limit_min",
            "passenger_limit_max",
            "age_limit",
            "departure",
            "destination",
            "locations",
            "country",
            "categories",
            "metadata",
            "is_featured",
            "is_pax_required",
            "is_active",
            "cancellation_policy",
            "created_at",
            "updated_at",
            "created_by",
            "host",
            "tags",
            # Additional Model relations.
            "trip_url",
            "trip_itinerary",
            "options",
        )

    @extend_schema_field({"type": "string", "example": "1 week 5 days"})
    def get_duration(self, obj):
        return str(obj.duration) if obj.duration else None

    @extend_schema_field(
        {"type": "string", "example": "api/v1/trips/2-days-trip-to-isb"}
    )
    def get_trip_url(self, trip):
        return reverse("trips-api:trip-detail", kwargs={"identifier": trip.slug})

    @extend_schema_field(OpenApiTypes.STR)
    def get_cancellation_policy(self, obj: "Trip") -> str:
        """Retrieve the trip's cancellation policy text.

        The trip-specific policy takes precedence over the host's default policy.
        Falls back to the current platform-wide policy if neither is set.

        Returns:
            str: The cancellation policy description text
        """
        return obj.cancellation_policy


class TripScheduleSerializer(serializers.ModelSerializer):
    trip = TripListSerializer()

    class Meta:
        model = TripSchedule
        fields = (
            "id",
            "trip",
            "price",
            "is_per_person_price",
            "start_date",
            "end_date",
            "available_seats",
            "booked_seats",
            "status",
        )


class UpcomingTripListSerializer(serializers.ModelSerializer):
    trip = TripListSerializer()

    class Meta:
        model = TripSchedule
        fields = (
            "id",
            "trip",
            "price",
            "is_per_person_price",
            "start_date",
            "end_date",
            "available_seats",
            "booked_seats",
            "status",
        )


class DestinationWithSchedulesSerializer(serializers.ModelSerializer):
    schedules = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ["id", "name", "slug", "schedules"]

    @extend_schema_field(UpcomingTripListSerializer(many=True))
    def get_schedules(self, obj: "Location"):
        schedules = TripSchedule.objects.upcoming().filter(
            id__in=obj.destination_trips.all().values_list("schedules", flat=True)
        )
        return UpcomingTripListSerializer(schedules, many=True).data


class TripBookingSerializer(serializers.ModelSerializer):
    schedule = serializers.PrimaryKeyRelatedField(
        queryset=TripSchedule.objects.upcoming(),
        write_only=True,
        help_text="ID of the selected trip schedule",
    )
    schedule_details = TripScheduleSerializer(
        source="schedule",
        read_only=True,
        help_text="Detailed information about the booking schedule ",
    )

    trip = TripDetailSerializer(read_only=True, help_text="Complete trip information")
    target_date = serializers.DateTimeField(
        help_text="The intended date for the trip (format: YYYY-MM-DDTHH:MM:SS)"
    )
    number_of_persons = serializers.IntegerField(
        min_value=1,
        max_value=50,
        help_text="Number of participants (1-50)",
    )

    RESTRICTED_FIELDS = (
        "trip",
        "schedule",
        "number",
        "status",
        "created_by",
    )

    class Meta:
        model = TripBooking
        fields = (
            "trip",
            "schedule",
            "schedule_details",
            "number",
            "status",
            "full_name",
            "email",
            "phone_number",
            "number_of_persons",
            "target_date",
            "message",
            "created",
            "created_by",
            "modified",
        )
        read_only_fields = ["number", "status", "created", "created_by", "modified"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        validated_data["created_by"] = self.context["request"].user

        trip = get_object_or_404(Trip.objects.active(), pk=self.context["trip_id"])
        if validated_data["schedule"].trip.pk != trip.pk:
            raise serializers.ValidationError(
                {"schedule": "The schedule must be the same as provided trip"}
            )
        return validated_data

    def create(self, validated_data):
        trip_schedule = super().create(validated_data)
        return trip_schedule

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if key not in self.RESTRICTED_FIELDS:
                setattr(instance, key, value)
        return instance


class TripBookingDetailSerializer(serializers.ModelSerializer):
    schedule = UpcomingTripListSerializer()
    trip = TripDetailSerializer(read_only=True)
    target_date = serializers.DateTimeField()
    number_of_persons = serializers.IntegerField()

    class Meta:
        model = TripBooking
        fields = (
            "trip",
            "schedule",
            "number",
            "status",
            "full_name",
            "email",
            "phone_number",
            "number_of_persons",
            "target_date",
            "message",
        )
        read_only_fields = ["number", "status", "created", "modified"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        trip = get_object_or_404(Trip.objects.active(), pk=self.context["trip_id"])
        if validated_data["schedule"].trip.pk != trip.pk:
            raise serializers.ValidationError(
                {"schedule": "The schedule must be the same as provided trip"}
            )
        return validated_data

    def create(self, validated_data):
        trip_schedule = super().create(validated_data)
        return trip_schedule
