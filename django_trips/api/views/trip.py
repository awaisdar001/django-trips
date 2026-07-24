# pylint:disable=import-error
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_trips.api.filters import TripFilter, UpcomingTripsFilter
from django_trips.api.paginators import CustomLimitOffsetPaginator
from django_trips.api.schema_meta import (
    destinations_list_schema,
    trip_create_schema,
    trip_delete_schema,
    trip_list_schema,
    trip_retrieve_schema,
    trip_update_schema,
    trip_wishlist_toggle_schema,
    upcoming_trips_list_schema,
)
from django_trips.api.serializers import (
    DestinationWithSchedulesSerializer,
    TripCreateSerializer,
    TripDetailSerializer,
    TripListSerializer,
    TripWishlistToggleSerializer,
    UpcomingTripListSerializer,
)
from django_trips.choices import ScheduleStatus
from django_trips.models import Location, Trip, TripSchedule, TripWishlist
from django_trips.permissions import IsStaffForDeleteOnly


@extend_schema_view(
    list=trip_list_schema,
    retrieve=trip_retrieve_schema,
    create=trip_create_schema,
    update=trip_update_schema,
    destroy=trip_delete_schema,
    wishlist=trip_wishlist_toggle_schema,
)
class TripViewSet(ModelViewSet):  # pylint:disable=too-many-ancestors
    """
    ViewSet for managing Trips with standard REST actions.

    Supports listing, creating, retrieving, updating, and deleting Trip instances.

    | Action    | HTTP Method | URL Pattern        | Reverse     | Description        |
    |-----------|-------------|--------------------|-------------|--------------------|
    | List      | GET         | /trips/            | trip-list   | Retrieve all trips |
    | Create    | POST        | /trips/            | trip-list   | Create a trip      |
    | Retrieve  | GET         | /trips/<id>/       | trip-detail | Retrieve a trip    |
    | Update    | PUT         | /trips/<id>/       | trip-detail | Update a trip      |
    | Delete    | DELETE      | /trips/<id>/       | trip-detail | Delete a trip      |

    Notes:
    - Partial updates (PATCH) are **not supported**.
    - Lookup field supports ID or slug as `{id}`.
    - List/retrieve (GET) are public; create/update require authentication;
      delete requires staff.

    Authentication: Session and JWT
    """

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffForDeleteOnly]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = CustomLimitOffsetPaginator

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TripFilter
    # DRF's OrderingFilter validates/orders by the literal client-supplied term
    # (a 2-tuple only supplies a display label, it isn't an alias) so the
    # annotation below must be named exactly `price` to make `?ordering=price`
    # work. It's still distinct from the `starting_price` model property:
    # annotating under that name would make Django try to setattr() a value
    # onto a property with no setter, raising AttributeError per row.
    ordering_fields = ["name", "duration", "price"]
    queryset = Trip.objects.active()

    serializer_class = TripDetailSerializer

    lookup_field = "identifier"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            # annotate() with an aggregate silently drops Trip.Meta's default
            # ordering (Django stops applying it once GROUP BY is involved),
            # so re-assert it explicitly here. Otherwise, with no ?ordering=
            # param, row order is whatever MySQL's query plan happens to
            # produce for that particular filter combination — same rows,
            # different order, from one request to the next.
            queryset = queryset.annotate(
                price=Min(
                    "schedules__price",
                    filter=Q(schedules__status=ScheduleStatus.PUBLISHED),
                )
            ).distinct().order_by(*Trip._meta.ordering)  # pylint:disable=protected-access
        return queryset

    def get_serializer_class(self):
        if self.action == "list":  # pylint:disable=no-else-return
            return TripListSerializer
        elif self.action == "retrieve":
            return TripDetailSerializer
        elif self.action in ["create", "update"]:
            return TripCreateSerializer
        return TripListSerializer

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        if identifier.isdigit():
            return get_object_or_404(Trip, pk=int(identifier))
        return get_object_or_404(Trip, slug=identifier)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context["wished_trip_ids"] = (
            set(TripWishlist.objects.filter(user=user).values_list("trip_id", flat=True))
            if user.is_authenticated
            else set()
        )
        return context

    @action(
        detail=True,
        methods=["post"],
        url_path="wishlist",
        permission_classes=[IsAuthenticated],
    )
    def wishlist(self, request, *args, **kwargs):  # pylint:disable=unused-argument
        """Toggle the current user's wishlist membership for this trip."""
        trip = self.get_object()
        wishlist_entry, created = TripWishlist.objects.get_or_create(
            user=request.user, trip=trip
        )
        if not created:
            wishlist_entry.delete()

        serializer = TripWishlistToggleSerializer({"is_wished": created})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip = serializer.save()

        response_serializer = TripDetailSerializer(
            trip, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        trip = self.get_object()
        response_serializer = TripDetailSerializer(
            trip, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, headers=headers)


@extend_schema_view(get=upcoming_trips_list_schema)
class UpcomingTripsListAPIView(ListAPIView):
    """
    API view to list upcoming (not-yet-started) trip schedules with optional filtering.

    Supports filtering trips by name, price range, date range, destination slug,
    and trip duration. Returns paginated list of trips with their schedule details.

    Public endpoint - no authentication required.

    Query parameters:
      - name: partial trip name (case-insensitive)
      - price_from: minimum price (inclusive)
      - price_to: maximum price (inclusive)
      - date_from: trips starting on or after this date (YYYY-MM-DD)
      - date_to: trips ending on or before this date (YYYY-MM-DD)
      - destination: exact slug of destination (case-insensitive)
      - duration_from: minimum trip duration in days (inclusive)
      - duration_to: maximum trip duration in days (inclusive)
    """

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    pagination_class = CustomLimitOffsetPaginator
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UpcomingTripsFilter
    ordering_fields = [
        "trip__name",
        "price",
        "start_date",
        "trip__duration",
    ]

    serializer_class = UpcomingTripListSerializer
    queryset = TripSchedule.objects.upcoming()


@extend_schema_view(get=destinations_list_schema)
class ActiveDestinationsWithSchedulesView(ListAPIView):
    """Public endpoint - no authentication required."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = DestinationWithSchedulesSerializer

    def get_queryset(self):
        return (
            Location.objects.active()
            .filter(destination_trips__isnull=False)
            .distinct()
            .prefetch_related("destination_trips")
        )
