import django_filters as filters
from django_trips.models import Trip, TripSchedule, TripBooking

from datetime import timedelta


class TimedeltaFromDaysFilter(filters.NumberFilter):
    def filter(self, qs, value):
        if value is not None:
            try:
                value = timedelta(days=float(value))
            except (ValueError, TypeError):
                return qs.none()
        return super().filter(qs, value)


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class TripBaseFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    destination = CharInFilter(
        field_name="trip__destination__slug",
        lookup_expr="in",
        help_text="Filter trips by a list of destination slugs, e.g. ?destination=hunza,skardu",
    )
    duration_from = filters.NumberFilter(field_name="duration", lookup_expr="gte")
    duration_to = filters.NumberFilter(field_name="duration", lookup_expr="lte")

    class Meta:
        model = Trip
        fields = []


class TripFilter(TripBaseFilter):

    class Meta(TripBaseFilter.Meta):
        model = Trip
        fields = []


class UpcomingTripsFilter(filters.FilterSet):
    """
    Filter upcoming trips by name, price range, date range, destination slug,
    and trip duration range (in days).
    """

    name = filters.CharFilter(
        field_name="trip__name",
        lookup_expr="icontains",
        help_text="Filter trips whose name contains this value (case-insensitive).",
    )
    price_from = filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        help_text="Filter trips with price greater than or equal to this value.",
    )
    price_to = filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        help_text="Filter trips with price less than or equal to this value.",
    )
    # "%Y-%m-%d"
    date_from = filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        help_text="Filter trips starting on or after this date (YYYY-MM-DD).",
    )
    date_to = filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        help_text="Filter trips ending on or before this date (YYYY-MM-DD).",
    )
    destination = CharInFilter(
        field_name="trip__destination__slug",
        lookup_expr="in",
        help_text="Filter trips by a list of destination slugs, e.g. ?destination=hunza,skardu",
    )
    duration_from = TimedeltaFromDaysFilter(
        field_name="trip__duration",
        lookup_expr="gte",
        help_text="Filter trips with duration greater than or equal to this many days.",
    )
    duration_to = TimedeltaFromDaysFilter(
        field_name="trip__duration",
        lookup_expr="lte",
        help_text="Filter trips with duration less than or equal to this many days.",
    )

    class Meta:
        model = TripSchedule
        fields = [
            "name",
            "price_from",
            "price_to",
            "date_from",
            "date_to",
            "destination",
            "duration_from",
            "duration_to",
        ]


class TripScheduleFilter(TripBaseFilter):
    price_from = filters.NumberFilter(
        label="Price From", field_name="trip_schedule__price", lookup_expr=("gte")
    )
    price_to = filters.NumberFilter(
        label="Price To", field_name="trip_schedule__price", lookup_expr=("lte")
    )

    date_from = filters.DateFilter(
        label="Trip Date From",
        field_name="trip_schedule__date_from",
        lookup_expr=("gte"),
    )
    end_date = filters.DateFilter(
        label="Trip Date To", field_name="trip_schedule__date_from", lookup_expr=("lte")
    )

    class Meta:
        model = TripBaseFilter.Meta.model
        fields = TripBaseFilter.Meta.fields


class TripBookingFilterSet(filters.FilterSet):
    target_date_after = filters.DateTimeFilter(
        field_name="target_date",
        lookup_expr="gte",
        help_text="Include trip bookings targeted on or after this datetime.",
    )
    target_date_before = filters.DateTimeFilter(
        field_name="target_date",
        lookup_expr="lte",
        help_text="Include trip bookings targeted on or before this datetime.",
    )

    class Meta:
        model = TripBooking
        fields = [
            "schedule",
            "schedule__trip",
            "target_date_before",
            "target_date_after",
            "number_of_persons",
        ]
