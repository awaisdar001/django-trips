# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions, viewsets

from api import serializers
from api.paginators import CustomResponsePagination
from trips.models import Trip


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """Trip Viewset"""
    pagination_class = CustomResponsePagination
    queryset = Trip.active.all()
    permission_classes = [
        permissions.AllowAny
    ]

    def get_serializer_class(self):
        """
        Overridden method which the serializer.

        Use different serializer for list and retrieve requests.
        """
        if self.action == 'list':
            return serializers.TripListSerializer
        if self.action == 'retrieve':
            return serializers.TripDetailSerializer
        return serializers.TripListSerializer
