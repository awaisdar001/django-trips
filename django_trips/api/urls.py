"""Url definitions for api"""
from django.urls import path

from api import views

app_name = 'trips-api'

urlpatterns = [
    path('trips/', views.TripListCreateAPIView.as_view(), name="trips"),
    path('trip/<int:pk>/', views.TripRetrieveUpdateDestroyAPIView.as_view(), name="trip-item"),
]
