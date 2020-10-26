"""Urls for trips app"""
from django.urls import path
from django_trips.api import views

app_name = "trips-api"

urlpatterns = [
    path('trips/', views.TripListCreateAPIView.as_view(), name="trips"),
    path('trip/<int:pk>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item"),
    path('trip/<slug:slug>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item-slug"),
]
