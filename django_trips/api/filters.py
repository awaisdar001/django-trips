import django_filters as filters
from django_trips.models import Trip, Location
from django.db.models import Q


class TripFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr=('icontains'))
    destination = filters.BaseInFilter(field_name="destination__slug")
    duration_from = filters.NumberFilter(field_name='duration', lookup_expr=('gte'))
    duration_to = filters.NumberFilter(field_name='duration', lookup_expr=('lte'))
    price_from = filters.NumberFilter(
        label="Price From",
        field_name='trip_schedule__price',
        method='filter_from'
    )
    price_to = filters.NumberFilter(
        label='Price To',
        field_name='trip_schedule__price',
        method='filter_to'
    )

    date_from = filters.DateFilter(
        label="Trip Date From",
        field_name='trip_schedule__date_from',
        method='filter_from',
    )
    date_to = filters.DateFilter(
        label="Trip Date To",
        field_name='trip_schedule__date_from',
        method='filter_to',
    )

    def filter_from(self, queryset, name, value):
        lookup = '__'.join([name, 'gte'])
        return queryset.filter(**{lookup: value}).distinct()

    def filter_to(self, queryset, name, value):
        lookup = '__'.join([name, 'lte'])
        return queryset.filter(**{lookup: value}).distinct()

    class Meta:
        model = Trip
        fields = ('destination',)
