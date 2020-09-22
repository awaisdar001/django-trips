# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from api import serializers
from api.paginators import CustomResponsePagination
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from trips.models import Trip


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """Trip Viewset"""
    pagination_class = CustomResponsePagination
    queryset = Trip.active.all()
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    serializers_mapping = {
        'list': serializers.TripListSerializer,
        'retrieve': serializers.TripDetailSerializer
    }

    def get_serializer_class(self):
        """
        Overridden method which the serializer.

        Use different serializer for list and retrieve requests.
        """
        return self.serializers_mapping.get(self.action, serializers.TripListSerializer)
