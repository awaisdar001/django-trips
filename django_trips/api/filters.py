import django_filters as filters
from django_trips.models import Trip


class TripBaseFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr=('icontains'))
    destination = filters.BaseInFilter(field_name="destination__slug")
    duration_from = filters.NumberFilter(field_name='duration', lookup_expr=('gte'))
    duration_to = filters.NumberFilter(field_name='duration', lookup_expr=('lte'))

    class Meta:
        model = Trip
        fields = ('destination',)


class TripAvailabilityFilter(TripBaseFilter):
    price_from = filters.NumberFilter(
        label="Price From", field_name='trip_availability__price', lookup_expr=('gte')
    )
    price_to = filters.NumberFilter(
        label='Price To', field_name='trip_availability__price', lookup_expr=('lte')
    )

    date_from = filters.DateFilter(
        label="Available From", field_name='trip_availability__date_to', method='filter_date_from',
    )
    date_to = filters.DateFilter(
        label="Available Upto", field_name='trip_availability__date_to', method='filter_date_to',
    )

    def filter_date_from(self, queryset, name, value):
        lookup = '__'.join([name, 'lt'])
        return queryset.exclude(**{lookup: value}).distinct()

    def filter_date_to(self, queryset, name, value):
        lookup = '__'.join([name, 'lte'])
        return queryset.filter(**{lookup: value}).distinct()

    class Meta:
        model = TripBaseFilter.Meta.model
        fields = TripBaseFilter.Meta.fields


class TripScheduleFilter(TripBaseFilter):
    price_from = filters.NumberFilter(
        label="Price From", field_name='trip_schedule__price', lookup_expr=('gte')
    )
    price_to = filters.NumberFilter(
        label='Price To', field_name='trip_schedule__price', lookup_expr=('lte')
    )

    date_from = filters.DateFilter(
        label="Trip Date From", field_name='trip_schedule__date_from', lookup_expr=('gte')
    )
    date_to = filters.DateFilter(
        label="Trip Date To", field_name='trip_schedule__date_from', lookup_expr=('lte')
    )

    class Meta:
        model = TripBaseFilter.Meta.model
        fields = TripBaseFilter.Meta.fields
