from enum import Enum

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from django_trips.api.serializers import (
    DestinationWithSchedulesSerializer,
    TripBookingSerializer,
    TripCreateSerializer,
    TripDetailSerializer,
    TripListSerializer,
)


# pylint:disable=all
class SchemaTags(Enum):
    TRIPS = ["Trips"]
    Bookings = ["Bookings"]


error_response_serializer = inline_serializer(
    name="ErrorResponse",
    fields={
        "detail": serializers.CharField(help_text="High-level error message"),
    },
)

trip_create_schema = extend_schema(
    summary="Create Trip",
    description="Create a new trip with details like itinerary, locations, facilities, gear, and tags.",
    request=TripCreateSerializer,
    responses={
        201: TripDetailSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
    },
    tags=SchemaTags.TRIPS.value,
)

trip_retrieve_schema = extend_schema(
    summary="Retrieve a Trip",
    description="Get detailed information of a trip by its ID or slug, including related itinerary, locations, "
    "facilities, and host info.",
    responses={200: TripDetailSerializer},
    parameters=[
        OpenApiParameter(
            "identifier",
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            description="Unique trip ID or slug to identify the trip.",
        )
    ],
    tags=SchemaTags.TRIPS.value,
)

trip_list_schema = extend_schema(
    summary="List Trips",
    description="Retrieve a paginated list of all available trips with summary information.",
    responses={200: TripListSerializer},
    tags=SchemaTags.TRIPS.value,
)


trip_update_schema = extend_schema(
    summary="Update a Trip",
    description="Fully update a trip by ID or slug. Partial updates (PATCH) are not supported.",
    request=TripCreateSerializer,
    parameters=[
        OpenApiParameter(
            "identifier",
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            description="Unique trip ID or slug to identify the trip.",
        )
    ],
    responses={
        200: TripDetailSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        404: OpenApiResponse(description="Trip not found"),
    },
    tags=SchemaTags.TRIPS.value,
)

trip_delete_schema = extend_schema(
    summary="Delete a Trip",
    description="Delete a trip by ID or slug. Only staff users are authorized to perform this action.",
    parameters=[
        OpenApiParameter(
            "identifier",
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            description="Unique trip ID or slug to identify the trip.",
        )
    ],
    responses={
        204: OpenApiResponse(
            description="Trip deleted successfully, no content returned"
        ),
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        403: OpenApiResponse(description="Permission denied"),
        404: OpenApiResponse(description="Trip not found"),
    },
    tags=SchemaTags.TRIPS.value,
)

upcoming_trips_list_schema = extend_schema(
    summary="Upcoming Trips",
    description="List all upcoming trips with filter.",
    tags=SchemaTags.TRIPS.value,
    responses={200: TripListSerializer},
    parameters=[
        OpenApiParameter(
            name="ordering",
            description="Ordering of results. Example: `start_date`, `-price`, `trip__duration`",
            required=False,
            type=OpenApiTypes.STR,
        ),
    ],
)
destinations_list_schema = extend_schema(
    summary="Get Trip Destinations",
    description="List all trip destinations.",
    responses={200: DestinationWithSchedulesSerializer},
    tags=SchemaTags.TRIPS.value,
)

booking_create_schema = extend_schema(
    summary="Book a trip",
    description="Creates a new booking for the specified trip",
    request=TripBookingSerializer,
    responses={
        201: TripBookingSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        403: OpenApiResponse(description="User not authorized to create booking"),
    },
    tags=SchemaTags.Bookings.value,
)

booking_list_schema = extend_schema(
    summary="List bookings",
    description=(
        "**Permission:** Admin users only. "
        "Get paginated trip bookings with essential details. Includes filtering, sorting and searching.",
    ),
    responses={
        200: TripBookingSerializer(many=True),
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
    },
    tags=SchemaTags.Bookings.value,
)


booking_retrieve_schema = extend_schema(
    summary="Get booking details",
    description="""  
    Retrieve complete details of a specific booking including trip information, 
    payment status, and participant details.
    """,
    responses={
        200: TripBookingSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        404: OpenApiResponse(description="Booking not found"),
    },
    tags=SchemaTags.Bookings.value,
)

booking_update_schema = extend_schema(
    summary="Update booking details",
    description="""  
    Update details of a specific booking e.g. contact details, no of persons,
    target date, message.
    """,
    responses={
        200: TripBookingSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        404: OpenApiResponse(description="Booking not found"),
    },
    tags=SchemaTags.Bookings.value,
)

booking_cancel_schema = extend_schema(
    summary="Cancel a trip booking",
    description="Cancel a booking identified by the number in the URL. Only allowed if the booking is not already cancelled and meets cancellation criteria.",
    responses={
        200: TripBookingSerializer,
        400: OpenApiResponse(
            response=error_response_serializer,
            description="Invalid input data",
        ),
        403: OpenApiResponse(description="Not authenticated or not permitted."),
        404: OpenApiResponse(description="Booking not found."),
    },
    tags=SchemaTags.Bookings.value,
)
