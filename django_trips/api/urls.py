from django.urls import path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework.routers import DefaultRouter

from django_trips.api.views import booking, trip
from django_trips.api.views.trip import (ActiveDestinationsWithSchedulesView,
                                         TripViewSet)

app_name = "trips-api"

router = DefaultRouter()
router.register(r"trips", TripViewSet, basename="trip")
router.register(
    r"trips/bookings", booking.TripBookingRetrieveUpdateViewSet, basename="booking"
)

app_urlpatterns = [
    path(
        "trips/upcoming/",
        trip.UpcomingTripsListAPIView.as_view(),
        name="upcoming-trips-list",
    ),
    path(
        "destinations/",
        trip.ActiveDestinationsWithSchedulesView.as_view(),
        name="destinations",
    ),
    # Trip Bookings endpoint.
    path(
        "trips/<int:trip_id>/bookings/",
        booking.TripBookingListView.as_view(),
        name="trip-bookings",
    ),
    path(
        "trips/<int:trip_id>/bookings/create/",
        booking.TripBookingCreateView.as_view(),
        name="trip-bookings-create",
    ),
    # path(
    #     "trips/bookings/<str:number>/",
    #     booking.TripBookingRetrieveUpdateAPIView.as_view(),
    #     name="booking-detail",
    # ),
    # path(
    #     "trip/bookings/",
    #     booking.TripBookingListCreateView.as_view(),
    #     name="create-booking",
    # ),
    # path(
    #     "trip/<slug:slug>/bookings/",
    #     booking.TripBookingsRetrieveAPIView.as_view(),
    #     name="trip-bookings",
    # ),
    *router.urls,
]

schema_urls = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="trips-api:schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="trips-api:schema"),
        name="redoc",
    ),
]

urlpatterns = [*app_urlpatterns, *schema_urls]

# NEXT:TripBookingRetrieveUpdateDestroyAPIView, action, tests
