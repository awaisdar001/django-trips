"""Urls for trips app"""
from django.urls import include, path

urlpatterns = [
    path('', include('django_trips.api.urls')),

]
