"""Urls for trips app"""
from django.urls import path
from django_trips.api import views

app_name = "trips-api"

urlpatterns = [
    path('trips/', views.TripListCreateAPIView.as_view(), name="trips"),
    path('destinations/', views.DestinationsListAPIView.as_view(), name="destinations"),
    path('destination/<slug:slug>/', views.DestinationsListAPIView.as_view(), name="destination-item"),

    path('trip/bookings', views.TripBookingsListCreateAPIView.as_view(), name="trips-bookings"),
    path('trip/<int:pk>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item"),
    path('trip/<slug:slug>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item-slug"),
]
