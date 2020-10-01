# -*- coding: utf-8 -*-

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class CustomResponsePagination(PageNumberPagination):
    """
    API Custom paginator to tell number of pages
    on which data has been distributed.
    """

    page_size = 10

    def get_paginated_response(self, data):
        """
        Return custom paginated response as
        {
        'next': next page
        'previous': previous page
        'count': Total records
        'current': Current Page
        'pages': Total number of pages
        'data': data returned by API
        }
        """
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'current': self.page.number,
            'pages': self.page.paginator.num_pages,
            'results': data,
        })
