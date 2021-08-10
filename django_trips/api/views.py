# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated

from django_trips.models import Trip, Location
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

        GET: Return all trips (paginated, 10per page.)
            /api/trips/
        GET: Search Trips that contains specific name.
            /api/trips/?name=Islamabad
            Other Options.
            | Keyword               |                                                                       |
            | name ""               | Find trips that contains specific name.                               |
            |                       | name=Trip to lahore OR name=chitral                                   |
            | destination[]         | Filter trips with specific destinations.                              |
            |                       | e.g. destination=islamabad,lahore                                     |
            | price_from (str)      | Find trips that has price greater than or equal to the given amount   |
            | price_to (str)        | Find trips that has price less than or equal to the given amount      |
            | duration_from (int)   | Find trips having duration greater than or equal to the given number  |
            | duration_to (int)     | Find trips having duration less  than or equal to the given number    |
            | date_from (date)      | Find trips that are scheduled greater than or specified date          |
            | date_to (date)        | Find trips that are scheduled less than or equal to specified date    |

        Examples:
            /api/trips/?
                destination=islamabad,lahore,fairy+meadows
                &name=trip
                &duration_from=1&duration_to=15
                &price_from=500&price_to=8000
                &date_from=2020-10-21&date_to=2020-11-11
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    pagination_class = TripResponsePagination
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


class DestinationsListAPIView(mixins.ListModelMixin, mixins.RetrieveModelMixin, generics.GenericAPIView):
    """
    Destination List view.
    This endpoint is used to list one or all the destinations using the GET request type.

    Examples:
        GET: Return all destinations (paginated, 10per page.)
            /api/destinations/

        GET: Return single destination
            /api/destination/gilgit/
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Location.destinations.all()
    serializer_class = serializers.DestinationMinimumSerializer
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        if self.lookup_field in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)
