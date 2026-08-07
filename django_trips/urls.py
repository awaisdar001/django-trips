"""Urls for trips app"""

from django.urls import include, path

urlpatterns = [
    path(
        "api/v1/",
        include(("django_trips.api.urls", "trips-api"), namespace="trips-api"),
    ),
]
