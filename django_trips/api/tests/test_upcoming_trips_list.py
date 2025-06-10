from datetime import timedelta
from unittest.mock import ANY
import factory
import ddt
import pytest
from django.urls import reverse
from django.utils import timezone

from django_trips.models import TripSchedule
from django_trips.tests.factories import (
    TripFactory,
    TripScheduleFactory,
    AuthenticatedUserTestCase,
    LocationFactory,
)

current_time = timezone.now().date()
seven_days_ago = current_time - timedelta(days=7)


@ddt.ddt
@pytest.mark.django_db
class TestUpcomingTripsListAPI(AuthenticatedUserTestCase):
    maxDiff = None
    url = reverse("trips-api:upcoming-trips-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        destinations = [
            LocationFactory(name="Swat"),
            LocationFactory(name="Hunza"),
            LocationFactory(name="Skardu"),
        ]
        departure_locations = [
            LocationFactory(name="Islamabad"),
            LocationFactory(name="Lahore"),
            LocationFactory(name="Jhelum"),
        ]
        cls.trips = TripFactory.create_batch(
            size=10,
            # Trip 1, Trip 2, Trip 10.
            name=factory.Iterator([f"Trip {i}" for i in range(1, 11)]),
            # 3 days -- 13 days
            duration=factory.Iterator([timedelta(days=i + 3) for i in range(1, 11)]),
            destination=factory.Iterator(destinations),
            departure=factory.Iterator(departure_locations),
        )

        cls.past_dates = [  # [-7 -6 -5 -4 -3 -2 -1 today 1 2]
            seven_days_ago + timedelta(days=i) for i in range(len(cls.trips))
        ]
        cls.future_dates = [  # [1 2 3 4 5 6 7 8 9 10]
            current_time + timedelta(days=i + 1) for i in range(len(cls.trips))
        ]

        base_price = 10000
        for trip in cls.trips[:2]:
            base_price += 1500
            TripScheduleFactory(
                trip=trip,
                start_date=factory.Iterator(cls.past_dates[:2]),
                end_date=factory.Iterator(cls.past_dates[:2][::-1]),
                price=base_price,
            )

        # Create 6 active trip schedules (start in-past, end in future)
        for trip in cls.trips[2:8]:
            base_price += 1000
            TripScheduleFactory(
                trip=trip,  # Trip 3 -- Trip 9
                start_date=factory.Iterator(cls.past_dates[2:8]),
                end_date=factory.Iterator(cls.future_dates[2:8]),
                # 13,000 -- 19,000
                price=base_price,
            )

        # Create 2 future trip schedules (start and end in the future)
        for trip in cls.trips[8:]:
            base_price += 5000
            TripScheduleFactory(
                trip=trip,
                start_date=factory.Iterator(cls.future_dates[:2]),
                end_date=factory.Iterator(cls.future_dates[8:]),
                price=base_price,
            )

    def get_trips_list_result(self, params=None, expected_code=200):
        """Get trip list by calling api and return results"""
        response = self.client.get(self.url, params, headers=self.headers)
        self.assertEqual(response.status_code, expected_code, response.json())
        return response.json()["results"]

    @ddt.data(
        *(
            ("Trip 1", 0),
            ("Trip 2", 0),
            ("Trip 3", 1),
            ("Trip 4", 1),
            ("Trip 5", 1),
            ("Trip 6", 1),
            ("Trip 7", 1),
            ("Trip 8", 1),
            ("Trip 9", 0),
            ("Trip 10", 0),
            ("Trip", 6),  # partial match
            ("trip", 6),  # case-insensitive
            ("Invalid", 0),  # no match
        )
    )
    @ddt.unpack
    def test_filter_by_name(self, search, expected_count):
        """Should return trips matching name (case-insensitive contains)"""
        data = self.get_trips_list_result({"name": search})
        self.assertEqual(len(data), expected_count, search)

    @ddt.data(
        *(
            (10000, 6),
            (11500, 6),
            (13000, 6),
            (14000, 6),
            (15000, 5),
            (16000, 4),
            (17000, 3),
            (18000, 2),
            (19000, 1),
            (20000, 0),
            (21000, 0),
        )
    )
    @ddt.unpack
    def test_filter_by_price_from(self, price, expected_count):
        """Should return trips with price >= price_from"""
        data = self.get_trips_list_result({"price_from": price})
        self.assertEqual(len(data), expected_count, price)

    @ddt.data(
        *(
            (10000, 0),
            (11500, 0),
            (13000, 0),
            (14000, 1),
            (15000, 2),
            (16000, 3),
            (17000, 4),
            (18000, 5),
            (19000, 6),
            (20000, 6),
            (21000, 6),
            (25000, 6),
        )
    )
    @ddt.unpack
    def test_filter_by_price_to(self, price, expected_count):
        """Should return trips with price <= price_to"""
        data = self.get_trips_list_result({"price_to": price})
        self.assertEqual(len(data), expected_count, price)

    @ddt.data(
        ("past-mid", current_time - timedelta(days=5)),
        ("future", current_time + timedelta(days=2)),
    )
    @ddt.unpack
    def test_filter_by_date_from(self, label, date):
        """Should return trips starting on/after the given date"""
        expected_slugs = {
            s.trip.slug
            for s in TripSchedule.objects.active().filter(start_date__gte=date)
        }
        data = self.get_trips_list_result({"date_from": date.isoformat()})
        response_slugs = {t["trip"]["slug"] for t in data}
        self.assertSetEqual(response_slugs, expected_slugs, msg=f"{label=} {date=}")

    @ddt.data(
        ("past-limit", current_time - timedelta(days=10), 0),
        ("future-limit", current_time + timedelta(days=10), 6),
    )
    @ddt.unpack
    def test_filter_by_date_to(self, label, date, expected_count):
        """Should return trips starting before/equal to date_to"""
        data = self.get_trips_list_result({"date_to": date.isoformat()})
        self.assertEqual(len(data), expected_count, msg=f"{label=} {date=}")

    def test_filter_by_destination(self):
        """Should filter trips by destination name (case-insensitive match)"""
        destinations = [self.trips[2].destination.slug, self.trips[1].destination.slug]
        query_params = {"destination": ",".join(destinations)}
        data = self.get_trips_list_result(query_params)

        response_trips = {item["trip"]["destination"]["slug"] for item in data}
        self.assertTrue(all(t in destinations for t in response_trips))

    def test_filter_by_duration_range(self):
        """Should return trips within duration range"""
        data = self.get_trips_list_result({"duration_from": 5, "duration_to": 8})
        durations = [item["trip"]["duration"] for item in data]
        for d in durations:
            d = int(d[0])
            self.assertGreaterEqual(d, 5)
            self.assertLessEqual(d, 8)

    def test_combined_filters(self):
        """Should apply multiple filters together"""
        query = {
            "price_from": 13000,
            "price_to": 17000,
            "duration_from": 5,
            "duration_to": 10,
        }
        data = self.get_trips_list_result(query)
        self.assertTrue(all(13000 <= int(t["price"]) <= 17000 for t in data))
        expected_durations = [f"{d} days, 0:00:00" for d in range(6, 10)]
        actual_durations = [t["trip"]["duration"] for t in data]
        self.assertEqual(actual_durations, expected_durations)

    def test_invalid_date_format(self):
        """Should return 400 for invalid date"""
        response = self.client.get(
            self.url, {"date_from": "not-a-date"}, headers=self.headers
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_query_returns_all(self):
        """Should return all active trips if no filters applied"""
        data = self.get_trips_list_result()
        self.assertEqual(len(data), 6)

    @ddt.data(
        ("price", "price"),
        ("price", "-price"),
        ("start_date", "start_date"),
        ("start_date", "-start_date"),
        ("trip__name", "trip__name"),
        ("trip__name", "-trip__name"),
    )
    @ddt.unpack
    def test_upcoming_trips_ordering(self, field, ordering):
        """Test ordering by various fields."""
        is_reverse = ordering.startswith("-")
        params = {"ordering": ordering}
        data = self.get_trips_list_result(params)

        fields = field.split("__")
        if len(fields) > 1:
            # For fields like 'trip__duration'
            response_data = [r[fields[0]][fields[1]] for r in data]
        else:
            response_data = [r[field] for r in data]

        self.assertEqual(
            response_data,
            sorted(response_data, reverse=is_reverse),
            f"{field} - {is_reverse} - {response_data}",
        )

    @ddt.data(
        ("trip__duration", "trip__duration"),
        ("trip__duration", "-trip__duration"),
    )
    @ddt.unpack
    def test_upcoming_trips_ordering_by_duration(self, field, ordering):
        """Test ordering by trip_duration field."""
        is_reverse = ordering.startswith("-")
        params = {"ordering": ordering}
        data = self.get_trips_list_result(params)

        fields = field.split("__")
        field_data = [int(r[fields[0]][fields[1]].split(" ")[0]) for r in data]

        self.assertEqual(
            field_data,
            sorted(field_data, reverse=is_reverse),
            f"Ordering by {field} (reverse={is_reverse}) failed! Result: {field_data}",
        )

    def test_me(self):
        """Test ordering by trip_duration field."""
        url = reverse("trips-api:destinations")
        response = self.client.get(self.url, {}, headers=self.headers)
