"""Urls for trips app"""
from django.urls import path, include


urlpatterns = [
    path('', include('django_trips.api.urls')),

]
