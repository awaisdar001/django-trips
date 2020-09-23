# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from api import serializers
from api.paginators import CustomResponsePagination
from trips.models import Trip


class TripListCreateAPIView(generics.ListCreateAPIView):
    """Create Trip view."""
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Trip.active.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.TripSerializerWithIDs
        return serializers.TripDetailSerializer


class TripRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Create Trip view."""
    pagination_class = CustomResponsePagination
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Trip.active.all()

    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.TripDetailSerializer
        return serializers.TripSerializerWithIDs
