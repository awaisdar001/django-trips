"""Urls for trips app"""
from django.urls import path
from django_trips.api import views

app_name = "trips-api"

urlpatterns = [
    path('trips/', views.TripListCreateAPIView.as_view(), name="trips"),
    path(
        'trips/by/availability/',
        views.TripListCreateAPIView.as_view(filter_by='availability'),
        name="trips-by-availability"
    ),

    # Destinations endpoints.
    path('destinations/', views.DestinationsListAPIView.as_view(), name="destinations"),
    path('destination/<slug:slug>/', views.DestinationsListAPIView.as_view(), name="destination-item"),

    # Trip Bookings endpoint.
    path('trip/bookings/', views.TripBookingCreateListAPIView.as_view(), name="create-booking"),
    path('trip/booking/<int:pk>/', views.TripBookingRetrieveUpdateAPIView.as_view(), name="retrieve-booking"),
    path('trip/<slug:slug>/bookings/', views.TripBookingsRetrieveAPIView.as_view(), name="trip-bookings"),

    # Trip details endpoint.
    # Note: Let them at the end of the list.
    path('trip/<int:pk>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item"),
    path('trip/<slug:slug>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item-slug"),
]
