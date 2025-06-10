from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_trips.api.filters import TripFilter, UpcomingTripsFilter
from django_trips.api.paginators import (
    CustomLimitOffsetPaginator,
)
from django_trips.api.schema_meta import (
    trip_create_schema,
    trip_list_schema,
    upcoming_trips_list_schema,
    trip_retrieve_schema,
    trip_delete_schema,
    trip_update_schema,
    destinations_list_schema,
)
from django_trips.api.serializers import (
    TripListSerializer,
    TripCreateSerializer,
    TripDetailSerializer,
    UpcomingTripListSerializer,
    DestinationWithSchedulesSerializer,
)
from django_trips.models import Trip, TripSchedule, Location
from django_trips.permissions import IsStaffForDeleteOnly


@extend_schema_view(
    list=trip_list_schema,
    retrieve=trip_retrieve_schema,
    create=trip_create_schema,
    update=trip_update_schema,
    destroy=trip_delete_schema,
)
class TripViewSet(ModelViewSet):
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
    - Staff-only permission applies to DELETE method.

    Authentication: Session and JWT
    """

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, IsStaffForDeleteOnly]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = CustomLimitOffsetPaginator

    filter_backends = [DjangoFilterBackend]
    filterset_class = TripFilter
    queryset = Trip.objects.active()

    serializer_class = TripDetailSerializer

    lookup_field = "identifier"

    def get_serializer_class(self):
        if self.action == "list":
            return TripListSerializer
        elif self.action == "retrieve":
            return TripDetailSerializer
        elif self.action in ["create", "update"]:
            return TripCreateSerializer
        return TripListSerializer  # fallback

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        if identifier.isdigit():
            return get_object_or_404(Trip, pk=int(identifier))
        return get_object_or_404(Trip, slug=identifier)

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
    API view to list upcoming trips with optional filtering.

    Supports filtering trips by name, price range, date range, destination slug,
    and trip duration. Returns paginated list of trips with their schedule details.

    Authentication is required to access this endpoint.

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
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UpcomingTripsFilter
    ordering_fields = [
        "trip__name",
        "price",
        "start_date",
        "trip__duration",
    ]

    serializer_class = UpcomingTripListSerializer
    queryset = TripSchedule.objects.active()


@extend_schema_view(get=destinations_list_schema)
class ActiveDestinationsWithSchedulesView(ListAPIView):
    serializer_class = DestinationWithSchedulesSerializer

    def get_queryset(self):
        return (
            Location.objects.active().prefetch_related("destination_trips").distinct()
        )
