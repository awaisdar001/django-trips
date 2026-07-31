"""Django Trips serializers"""

from typing import TYPE_CHECKING, Optional

import crum
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_countries.serializer_fields import CountryField
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

from django_trips.choices import LocationType, ScheduleStatus
from django_trips.models import (
    Category,
    Facility,
    Gear,
    Host,
    Location,
    Testimonial,
    Trip,
    TripBooking,
    TripImage,
    TripItinerary,
    TripPackage,
    TripPickupLocation,
    TripReview,
    TripReviewSummary,
    TripSchedule,
    TrustBadge,
)
from django_trips.utils import format_trip_duration

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile


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
        fields = ("name", "slug", "icon")


class CategoryListSerializer(CategorySerializer):
    """
    Category serializer for the public category/activities listing.

    trips_count must come from an annotated queryset (see
    ActiveCategoriesListAPIView) - it's kept off the base CategorySerializer
    because that one is also used to nest categories inside Trip
    serializers, where no such annotation exists.
    """

    trips_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ("trips_count",)


class LocationSerializer(serializers.ModelSerializer):
    """Location Modal Serializer"""

    type = serializers.SerializerMethodField()
    region = serializers.ReadOnlyField()
    poster = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            "name",
            "slug",
            "travel_tips",
            "lat",
            "lon",
            "type",
            "region",
            "importance",
            "poster",
        )

    @extend_schema_field({"type": "string", "example": "TOWN"})
    def get_type(self, location):
        """Returns human readable model choice value."""
        return location.get_type_display()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_poster(self, location: "Location") -> Optional[str]:
        return get_location_poster(location, self.context)


class FacilitySerializer(serializers.ModelSerializer):
    """Facility Modal Serializer"""

    class Meta:
        model = Facility
        fields = ("id", "name", "slug", "icon", "is_active")


class TrustBadgeSerializer(serializers.ModelSerializer):
    """Trust Badge Modal Serializer"""

    class Meta:
        model = TrustBadge
        fields = ("id", "name", "slug", "icon", "is_active")


class TrustBadgeListSerializer(TrustBadgeSerializer):
    """
    Trust badge serializer for the public trust-badge filter listing.

    trips_count must come from an annotated queryset (see
    ActiveTrustBadgesListAPIView) - kept off the base TrustBadgeSerializer
    since that one is also used nested inside Trip serializers, where no
    such annotation exists.
    """

    trips_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(TrustBadgeSerializer.Meta):
        fields = TrustBadgeSerializer.Meta.fields + ("trips_count",)


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
        return host.type.name if host.type else ""

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
        host_rating = getattr(host, "ratings", None)
        if host_rating:
            rating["rating_count"] = host_rating.rating_count
            rating["rated_by"] = host_rating.rated_by
        return rating


class HostListSerializer(serializers.ModelSerializer):
    """
    Host serializer for the public host filter listing.

    Deliberately not built on HostSerializer: this only needs name/slug/count
    for a filter checklist, and HostSerializer's rating/cancellation_policy
    fields would add an avoidable per-host `ratings` lookup for data this
    list never shows. trips_count must come from an annotated queryset (see
    ActiveHostsListAPIView).
    """

    trips_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Host
        fields = ("name", "slug", "trips_count")


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
    trust_badges = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=TrustBadge.objects.active(),
        help_text="Trust badge identifiers for this trip (e.g. certified guide, free cancellation).",
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
            "trust_badges",
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
            "featured",
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
        trust_badges = validated_data.pop("trust_badges", [])
        gear = validated_data.pop("gear", [])
        categories = validated_data.pop("categories", [])
        tags = validated_data.pop("tags", [])

        # Create trip instance
        trip = super().create({"created_by": user, **validated_data})

        # Add M2M relationships
        trip.locations.set(locations)
        trip.facilities.set(facilities)
        trip.trust_badges.set(trust_badges)
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
        trust_badges = validated_data.pop("trust_badges", None)
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
        if trust_badges is not None:
            instance.trust_badges.set(trust_badges)
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


class TripReviewSummarySerializer(serializers.ModelSerializer):
    """Aggregate rating breakdown for a trip (curated, not auto-computed)."""

    class Meta:
        model = TripReviewSummary
        fields = ("meals", "accommodation", "transport", "value_for_money", "overall")


class TripReviewSerializer(serializers.ModelSerializer):
    """
    A single traveler review, for the paginated per-trip review list
    (`GET /trips/<trip_id>/reviews/`) - distinct from `TripReviewSummarySerializer`,
    which is the curated aggregate rollup shown on the trip card/header.
    Deliberately excludes `email` - a reviewer's contact info has no business
    being public.
    """

    location = serializers.SerializerMethodField()

    class Meta:
        model = TripReview
        fields = (
            "id",
            "name",
            "location",
            "meals",
            "accommodation",
            "transport",
            "value_for_money",
            "overall",
            "comment",
            "created_at",
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_location(self, review: "TripReview") -> Optional[str]:
        return review.location.name if review.location else None


def get_trip_review_summary_data(trip):
    """
    Build the review_summary dict for a trip: its curated rating breakdown
    (or all-zero defaults if none has been curated yet) plus a count of its
    verified reviews.

    Shared by TripListSerializer and TripDetailSerializer - not a
    SerializerMethodField on a mixin, since DRF's ModelSerializer silently
    falls back to auto-building a field from the model/relation when a
    same-named field is declared on a plain (non-Serializer) base class
    instead of directly on the serializer itself.
    """
    summary = getattr(trip, "review_summary", None)
    data = (
        TripReviewSummarySerializer(summary).data
        if summary
        else {
            "meals": 0,
            "accommodation": 0,
            "transport": 0,
            "value_for_money": 0,
            "overall": 0,
        }
    )
    data["reviews_count"] = trip.reviews.filter(is_verified=True).count()
    return data


class TripImageSerializer(serializers.ModelSerializer):
    """A single photo in a trip's gallery/carousel."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = TripImage
        fields = ("id", "image", "alt_text", "order")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image(self, obj: "TripImage") -> Optional[str]:
        return resolve_media_url(obj.image_upload, obj.image, self.context)


def resolve_media_url(
    upload_file: Optional["FieldFile"], url: Optional[str], context: dict
) -> Optional[str]:
    """
    Absolute URL for an "upload or external URL" media pair, or None if
    neither is set.

    `upload_file` (e.g. an ImageField) takes priority over `url` (a plain
    URLField/string) when both are set. `upload_file.url` is relative to
    MEDIA_URL, so it needs `request` from the serializer context to become
    an absolute URL matching `url`'s shape.
    """
    if upload_file:
        request = context.get("request")
        file_url = upload_file.url
        return request.build_absolute_uri(file_url) if request else file_url
    return url or None


def get_location_poster(location: "Location", context: dict) -> Optional[str]:
    """Absolute URL of a location's poster photo, or None if neither
    `poster_image` nor `poster_url` is set."""
    return resolve_media_url(location.poster_image, location.poster_url, context)


def get_trip_poster(trip: "Trip", context: dict) -> Optional[str]:
    """Absolute URL of a trip's primary listing photo, or None if neither
    `poster_image` nor `poster_url` is set."""
    return resolve_media_url(trip.poster_image, trip.poster_url, context)


def get_is_wished(trip, context):
    """
    Whether the current authenticated request user has wishlisted this trip.

    Prefers the `wished_trip_ids` set precomputed once per request by
    TripViewSet.get_serializer_context (avoids an `exists()` query per trip
    on list endpoints); falls back to a direct query when that context isn't
    present, e.g. TripDetailSerializer nested inside TripBookingSerializer.
    """
    wished_trip_ids = context.get("wished_trip_ids")
    if wished_trip_ids is not None:
        return trip.id in wished_trip_ids

    request = context.get("request")
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    return trip.wishlisted_by.filter(user=user).exists()


class TripWishlistToggleSerializer(serializers.Serializer):  # pylint:disable=abstract-method
    """Response body for the trip wishlist toggle action."""

    is_wished = serializers.BooleanField(read_only=True)


class TripScheduleBaseSerializer(serializers.ModelSerializer):
    """Fields shared by every context a `TripSchedule` is rendered in."""

    seats_left = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = TripSchedule
        fields = (
            "id",
            "price",
            "child_price",
            "is_per_person_price",
            "start_date",
            "end_date",
            "available_seats",
            "booked_seats",
            "seats_left",
            "status",
            "is_active",
        )


def get_upcoming_published_schedules(trip: "Trip"):
    """
    Queryset of a trip's upcoming, published departures - i.e. exactly what a
    traveler can actually book. Matches the `TripSchedule.objects.upcoming()`
    queryset `TripBookingSerializer`'s `schedule` field validates against, not
    every schedule row that happens to exist (draft/past/cancelled ones are
    irrelevant to an availability picker).
    """
    return (
        trip.schedules.upcoming()
        .filter(status=ScheduleStatus.PUBLISHED)
        .order_by("start_date")
    )


class TripListSerializer(serializers.ModelSerializer):
    destination = LocationSerializer()
    duration = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()
    images = TripImageSerializer(many=True, read_only=True)
    starting_price = serializers.ReadOnlyField()
    review_summary = serializers.SerializerMethodField()
    trip_url = serializers.SerializerMethodField()
    is_wished = serializers.SerializerMethodField()
    country = CountryField()
    categories = CategorySerializer(many=True)
    facilities = FacilitySerializer(many=True)
    trust_badges = TrustBadgeSerializer(many=True)
    host = HostSerializer()
    schedules = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "name",
            "slug",
            "description",
            "destination",
            "duration",
            "poster",
            "images",
            "starting_price",
            "review_summary",
            "country",
            "categories",
            "facilities",
            "trust_badges",
            "passenger_limit_min",
            "passenger_limit_max",
            "featured",
            "trip_url",
            "is_wished",
            "host",
            "schedules",
        )

    @extend_schema_field({"type": "string", "example": "7 Days 6 Nights"})
    def get_duration(self, obj):
        return format_trip_duration(obj.duration)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_poster(self, trip: "Trip") -> Optional[str]:
        return get_trip_poster(trip, self.context)

    @extend_schema_field(TripReviewSummarySerializer)
    def get_review_summary(self, obj):
        return get_trip_review_summary_data(obj)

    @extend_schema_field(
        {"type": "string", "example": "api/v1/trips/2-days-trip-to-isb"}
    )
    def get_trip_url(self, trip):
        return reverse("trips-api:trip-detail", kwargs={"identifier": trip.slug})

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_wished(self, trip):
        return get_is_wished(trip, self.context)

    @extend_schema_field(TripScheduleBaseSerializer(many=True))
    def get_schedules(self, trip):
        """
        Same upcoming/published departures as `TripDetailSerializer.schedules`,
        without `pickup_locations` - irrelevant until a traveler is actually
        booking, and needlessly heavy to prefetch for every card on `/trips/`.

        Prefers the `_prefetched_upcoming_schedules` cache `TripViewSet.get_queryset`
        attaches via `Prefetch(..., to_attr=...)` for the list action, to avoid an
        N+1 query per row; falls back to a direct query otherwise.
        """
        schedules = getattr(trip, "_prefetched_upcoming_schedules", None)
        if schedules is None:
            schedules = get_upcoming_published_schedules(trip)
        return TripScheduleBaseSerializer(schedules, many=True, context=self.context).data


class TripItineraryReadSerializer(BaseTripItinerarySerializer):
    location = LocationSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta(BaseTripItinerarySerializer.Meta):
        fields = BaseTripItinerarySerializer.Meta.fields


class TripPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPackage
        fields = ("name", "description", "base_price", "base_child_price")


class TripPickupLocationSerializer(serializers.ModelSerializer):
    """A pickup point offered for a specific trip departure."""

    name = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = TripPickupLocation
        fields = ("id", "name", "additional_price")


class TripScheduleDetailSerializer(TripScheduleBaseSerializer):
    """
    Nested under `TripDetailSerializer` - the parent trip is already known
    from context there, so this deliberately doesn't re-embed `trip` the way
    `TripScheduleSerializer` does.
    """

    pickup_locations = TripPickupLocationSerializer(many=True, read_only=True)

    class Meta(TripScheduleBaseSerializer.Meta):
        fields = TripScheduleBaseSerializer.Meta.fields + ("pickup_locations",)


class TripDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    cancellation_policy = serializers.SerializerMethodField()
    refund_schedule = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    poster = serializers.SerializerMethodField()
    images = TripImageSerializer(many=True, read_only=True)
    starting_price = serializers.ReadOnlyField()
    review_summary = serializers.SerializerMethodField()
    trip_url = serializers.SerializerMethodField()
    is_wished = serializers.SerializerMethodField()
    facilities = FacilitySerializer(many=True)
    trust_badges = TrustBadgeSerializer(many=True)
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
    packages = TripPackageSerializer(many=True)
    schedules = serializers.SerializerMethodField()

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
            "trust_badges",
            "gear",
            "poster",
            "images",
            "starting_price",
            "review_summary",
            "passenger_limit_min",
            "passenger_limit_max",
            "age_limit",
            "departure",
            "destination",
            "locations",
            "country",
            "categories",
            "metadata",
            "featured",
            "is_pax_required",
            "is_active",
            "cancellation_policy",
            "refund_schedule",
            "created_at",
            "updated_at",
            "created_by",
            "host",
            "tags",
            "is_wished",
            # Additional Model relations.
            "trip_url",
            "trip_itinerary",
            "packages",
            "schedules",
        )

    @extend_schema_field({"type": "string", "example": "7 Days 6 Nights"})
    def get_duration(self, obj):
        return format_trip_duration(obj.duration)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_poster(self, trip: "Trip") -> Optional[str]:
        return get_trip_poster(trip, self.context)

    @extend_schema_field(TripReviewSummarySerializer)
    def get_review_summary(self, obj):
        return get_trip_review_summary_data(obj)

    @extend_schema_field(
        {"type": "string", "example": "api/v1/trips/2-days-trip-to-isb"}
    )
    def get_trip_url(self, trip):
        return reverse("trips-api:trip-detail", kwargs={"identifier": trip.slug})

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_wished(self, trip):
        return get_is_wished(trip, self.context)

    @extend_schema_field(OpenApiTypes.STR)
    def get_cancellation_policy(self, obj: "Trip") -> str:
        """Retrieve the trip's cancellation policy text.

        The trip-specific policy takes precedence over the host's default policy.
        Falls back to the current platform-wide policy if neither is set.

        Returns:
            str: The cancellation policy description text
        """
        return obj.cancellation_policy

    @extend_schema_field(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "example": "7+ days before departure"},
                    "min_hours_before_departure": {"type": "integer", "example": 168},
                    "refund_percent": {"type": "integer", "example": 100},
                },
            },
        }
    )
    def get_refund_schedule(self, obj: "Trip"):
        """Structured refund tiers backing the cancellation-policy timeline UI
        (e.g. "7+ days: 100% / 3-7 days: 50% / <72hrs: 0%") - same host-override
        -over-platform-default precedence as `cancellation_policy` above."""
        return obj.refund_schedule

    @extend_schema_field(TripScheduleDetailSerializer(many=True))
    def get_schedules(self, trip):
        """Same as `TripListSerializer.schedules`, plus `pickup_locations` -
        only needed once a traveler is actually looking at a single trip to book."""
        schedules = get_upcoming_published_schedules(trip).prefetch_related(
            "pickup_locations__location"
        )
        return TripScheduleDetailSerializer(
            schedules, many=True, context=self.context
        ).data


class TripScheduleSerializer(TripScheduleBaseSerializer):
    """Used where the parent trip isn't already known from context, e.g. a
    booking's `schedule_details` or the standalone upcoming-trips list."""

    trip = TripListSerializer()

    class Meta(TripScheduleBaseSerializer.Meta):
        fields = ("trip",) + TripScheduleBaseSerializer.Meta.fields


class UpcomingTripListSerializer(TripScheduleSerializer):
    """Same shape as `TripScheduleSerializer` - kept as a distinct name for
    the `/trips/upcoming/` endpoint's schema/call sites."""


class DestinationWithSchedulesSerializer(serializers.ModelSerializer):
    """
    trips_count must come from an annotated queryset (see
    ActiveDestinationsWithSchedulesView) - it's used to rank destinations by
    popularity (e.g. a landing page's "top destinations") without a manual
    curation field.
    """

    schedules = serializers.SerializerMethodField()
    region = serializers.ReadOnlyField()
    trips_count = serializers.IntegerField(read_only=True, default=0)
    poster = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ["id", "name", "slug", "region", "schedules", "trips_count", "poster"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_poster(self, obj: "Location") -> Optional[str]:
        return get_location_poster(obj, self.context)

    @extend_schema_field(UpcomingTripListSerializer(many=True))
    def get_schedules(self, obj: "Location"):
        # A REGION-type location's own trips_count/schedules are rolled up
        # from its child locations (see ActiveDestinationsWithSchedulesView),
        # so the schedules nested here must match - otherwise a region could
        # report e.g. trips_count=3 with an empty schedules list. Scoped to
        # type=REGION specifically, same as the view - a CITY with children
        # (e.g. Skardu with Shangrila) doesn't roll its children up.
        destination_q = Q(destination=obj)
        if obj.type == LocationType.REGION:
            destination_q |= Q(destination__parent=obj)
        trips = Trip.objects.filter(destination_q)
        schedules = TripSchedule.objects.upcoming().filter(
            id__in=trips.values_list("schedules", flat=True)
        )
        return UpcomingTripListSerializer(schedules, many=True).data


class TestimonialSerializer(serializers.ModelSerializer):
    """Curated, site-wide marketing quote for landing-page social proof."""

    location = serializers.SerializerMethodField()

    class Meta:
        model = Testimonial
        fields = ["id", "quote", "name", "location"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_location(self, obj: "Testimonial") -> Optional[str]:
        return obj.location.name if obj.location else None


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
        request_user = self.context["request"].user
        validated_data["created_by"] = (
            request_user if request_user.is_authenticated else None
        )

        trip = get_object_or_404(Trip.objects.active(), pk=self.context["trip_id"])
        if validated_data["schedule"].trip.pk != trip.pk:
            raise serializers.ValidationError(
                {"schedule": "The schedule must be the same as provided trip"}
            )
        return validated_data

    def create(self, validated_data):
        number_of_persons = validated_data["number_of_persons"]

        with transaction.atomic():
            # Lock the schedule row so two concurrent bookings can't both
            # read the same remaining-seats count and both succeed.
            schedule = TripSchedule.objects.select_for_update().get(
                pk=validated_data["schedule"].pk
            )
            remaining_seats = schedule.seats_left
            if number_of_persons > remaining_seats:
                raise serializers.ValidationError(
                    {
                        "number_of_persons": (
                            f"Only {remaining_seats} seat(s) left "
                            "for this schedule."
                        )
                    }
                )

            trip_booking = super().create(validated_data)

            schedule.booked_seats += number_of_persons
            schedule.save(update_fields=["booked_seats"])

        return trip_booking

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if key not in self.RESTRICTED_FIELDS:
                setattr(instance, key, value)
        return instance
