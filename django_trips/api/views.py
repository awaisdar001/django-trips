# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, mixins
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated

from django_trips.models import Location, Trip, TripBooking
from . import serializers
from .filters import TripAvailabilityFilter, TripScheduleFilter
from .mixins import StaffOnlyDeleteOperationMixin, MultipleFieldLookupMixin
from .paginators import TripBookingsPagination, TripResponsePagination


class TripListCreateAPIView(generics.ListCreateAPIView):
    """
    **Use Cases**

        Retrieve the list of trips matching a given critaria, retrive trips details,
        and post a new trip.

    **Example Requests**:
        
        GET /api/trips/
        
        GET /api/trips/?name=Islamabad

        GET /api/trips/?
                destination=islamabad,lahore,fairy+meadows
                &name=trip
                &duration_from=1&duration_to=15
                &price_from=500&price_to=8000
                &date_from=2020-10-21&date_to=2020-11-11

        POST: /api/trips/
    
    
    **Other Search Params**

        | Keyword               |        Details                                                        |
        |-----------            |-----------                                                            |
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

    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    pagination_class = TripResponsePagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    queryset = Trip.active.all()

    # filter by param is passed from the urls.py
    filter_by = ''

    @property
    def filter_class(self):
        if self.filter_by == 'availability':
            return TripAvailabilityFilter
        return TripScheduleFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.TripSerializerWithIDs
        return serializers.TripDetailSerializer


class TripRetrieveUpdateDestroyAPIView(
    MultipleFieldLookupMixin,
    StaffOnlyDeleteOperationMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    **Use Cases**
        
        Retrieve, modify details of a trip or delete an existing trip.

    **Example Requests**:
        
        GET /api/trip/trip_id/
        
        GET /api/trip/trip_slug/
        
        PUT  /api/trip/99/
        {
            ...
            title: "updated title"
            age_limit: 39
        }

        PATCH  /api/trip/trip_id/
        { age_limit: 39 }

        DELETE /api/trip/trip_id/
    
    **GET Trip Parameters**:

        * trip_id (required): The trip to retrieve details for

        * trip_slug (required): The trip to retrieve details for

    **PATCH Parameters**:

        * age_limit (optional): An integer value to indicate trip age limit.

        Any trip param can be used in this request type. 

    **GET response values:
        
        *Coming soon...*

    **DELETE response values:

        Response 204 with no content is returned for a DELETE request
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
    **Use Cases**
        Retrieve all or specific destination details.

    **Example Requests**:
        
        GET /api/destinations/
        
        GET /api/destination/trip_slug/

    **GET Trip Parameters**:

        trip_slug (optional): Slug of the destination to get information for

    **GET response values:

        * name: The name of the location
        
        * slug: The slug of the location

        * coordinates: The latitude,longitude of the location

        * location_url: the relative url of the location details api URL

    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Location.objects.all()
    serializer_class = serializers.LocationSerializer

    def get_queryset(self, *args, **kwargs):
        """
        Todo -- replace with queryset class variable. 
        """
        return Location.objects.exclude(trip_destination__destination__isnull=True)

    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        if self.lookup_field in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)


class TripBookingCreateListAPIView(generics.ListCreateAPIView):
    """
    **Use Cases**
    
        Add new trip booking, retrieve all trip bookings or search trip bookings.

    **Example Requests**:

        GET /api/trip/bookings/

        GET /api/trip/bookings/?search=at%20Gharo

        POST /api/trip/bookings/
            {
              "name": "tom latham",
              "trip": "5-days-trip-to-jhelum",
              "phone_number": "tom",
              "cnic_number": "1234234-23423",
              "email": "a@gmail.com",
              "target_date": "2021-09-01",
              "message": "Tom booking# 1"
            }
    
    **POST Trip Booking Parameters**:

        * name(required): Name of person booking a trip
        
        * trip(required): trip slug to create booking for
        
        * phone_number(required): Person's contact number.
        
        * cnic_number(required): Person's cnic number.
        
        * email(required): Person's email address
        
        * target_date(required): booking date for the trip
        
        * message(optional): any additional information for the trip booking

    **GET Trip Booking Parameters**:
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TripBooking.objects.all()
    pagination_class = TripBookingsPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'trip__name', 'email', 'phone_number', 'cnic_number']

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.TripBookingCreateSerializer
        return serializers.TripBookingSerializer


class TripBookingRetrieveUpdateAPIView(
    StaffOnlyDeleteOperationMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    **Use Cases**
        
        Retrieve details a trip booking, update existing trip booking or delete existing
        trip booking.

    **Example Requests**:

        GET /api/trip/booking/pk/

        PATCH /api/trip/booking/pk/
        {
              "name": "tom latham",
              "trip": "5-days-trip-to-jhelum",
              "phone_number": "tom",
              "cnic_number": "1234234-23423",
              "email": "a@gmail.com",
              "target_date": "2021-09-01",
              "message": "Tom booking# 1"
        }

        DELETE /api/trip/booking/pk/

    **GET Trip Parameters**:

        pk (required): id of the trip booking

    **DELETE response values:**

        No content is returned for a DELETE request
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.TripBookingSerializer
    queryset = TripBooking.objects.all()
    lookup_fields = ['pk']


class TripBookingsRetrieveAPIView(generics.ListAPIView):
    """
    **Use Cases:**

        Retrieve all bookings of a single trip.


    **Example Requests:**

        GET /api/trip/trip_slug/bookings/

        GET /api/trip/trip_slug/bookings/?search=at%20Gharo

    **Search by:**

        GET /api/trip/trip_slug/bookings/?search=at%20Gharo
        Search term may contain the following.
        > trip name, > booking name, > booking email, > phone_number, > cnic number.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.TripBookingSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'trip__name', 'email', 'phone_number', 'cnic_number']

    def get_queryset(self, *args, **kwargs):
        return TripBooking.objects.filter(Q(trip__slug=self.kwargs['slug']))
