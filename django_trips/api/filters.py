import django_filters
from trips.models import Trip


class TripFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr=('icontains'))
    duration = django_filters.NumberFilter(field_name='duration', lookup_expr=('gte'))
    price = django_filters.NumberFilter(field_name='trip_schedule__price', method='filter_price')
    destination = django_filters.CharFilter(field_name='destination', method='filter_price')

    from_date = django_filters.DateFilter(
        label="Trip From Date",
        field_name='trip_schedule__date_from',
        method='filter_from_date',
    )
    to_date = django_filters.DateFilter(
        label="Trip To Date",
        field_name='trip_schedule__date_from',
        method='filter_to_date',
    )

    def filter_from_date(self, queryset, name, value):
        lookup = '__'.join([name, 'gte'])
        return queryset.filter(**{lookup: value})

    def filter_to_date(self, queryset, name, value):
        lookup = '__'.join([name, 'lte'])
        return queryset.filter(**{lookup: value})

    def filter_price(self, queryset, name, value):
        lookup = '__'.join([name, 'gte'])
        return queryset.filter(**{lookup: value})

    class Meta:
        model = Trip
        fields = ('name', 'price')
