# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from django_trips.models import Trip
from rest_framework import generics
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated

from . import serializers
from .filters import TripFilter
from .mixins import MultipleFieldLookupMixin
from .paginators import TripResponsePagination


class TripListCreateAPIView(generics.ListCreateAPIView):
    """
    Trips List and Create Trip view.

    This endpoint is used to list all the trips Using the GET request type.
    This endpoint is used to create a single trip using the POST request type. Provide all required data in
    the request body.

    Examples:
        POST: Creates a new trip
            /api/trips/
            data = {
                "name":"3 days trip to Islamabad",
                "description": "This is the description for trip: 66",
                "locations": [1,2],
                "facilities": [1,2],
                "destination": 1,
                "created_by": 1,
                "host": 1,
            }

        GET: Return all trips (paginated, 10per page.)
            /api/trips/
        GET: Search Trips that contains specific name.
            /api/trips/?name=Islamabad
            Other Options.
            | Keyword       |                                                                       |
            | name          | Find trips that contains specific name.                               |
            | price         | Find trips that contains price greater than or equal                  |
            | duration      | Find trips of duration greater than or equal                          |
            | from_date     | Find trips that are scheduled greater than or specified date          |
            | to_date       | Find trips that are scheduled less than or equal to specified date    |

    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filter_class = TripFilter
    queryset = Trip.active.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.TripSerializerWithIDs
        return serializers.TripDetailSerializer


class TripRetrieveUpdateDestroyAPIView(
    MultipleFieldLookupMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    Trip retrieve/update/destroy API View.

    This endpoint is used to fetch a single trip using GET request type.
    This endpoint is used to update a single trip using PUT request type.
    This endpoint is used to partially update a single trip using PATCH request type.
    This endpoint is used to delete a single trip using DELETE request type.

    Examples:
        GET: Fetch Trip by ID/Slug
            api/trip/99/
            api/trip/5-days-trip-to-jhelum/

        PUT: Update the whole object.
            api/trip/99/
            data = {
                ...
                age_limit: 39
            }

        PATCH: Partially update object values
            data = {age_limit: 39}
    """

    pagination_class = TripResponsePagination
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Trip.active.all()

    lookup_fields = ['pk', 'slug']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.TripDetailSerializer
        return serializers.TripSerializerWithIDs
