from datetime import timedelta
from unittest.mock import ANY

import ddt
import pytest
from django.urls import reverse
from django.utils import timezone

from django_trips.choices import ScheduleStatus
from django_trips.models import Trip
from django_trips.tests.factories import (AuthenticatedUserTestCase,
                                          CategoryFactory, HostFactory,
                                          LocationFactory, TripFactory,
                                          TripScheduleFactory)


@ddt.ddt
@pytest.mark.django_db
class TestTripListAPI(AuthenticatedUserTestCase):
    maxDiff = None
    url = reverse("trips-api:trip-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.trip = TripFactory.create(
            locations=["Lahore", "Gilgit"],
            facilities=["Transport", "Food"],
            gear=["Backpack", "Glasses"],
            categories=["Outdoors", "Hiking"],
        )
        date_in_past = timezone.now() - timedelta(days=7)
        cls.trip_schedule = TripScheduleFactory(trip=cls.trip, start_date=date_in_past)

    def get_trips_list_result(self):
        """Get trip list by calling api and return results"""
        response = self.client.get(self.url, {}, headers=self.headers)
        return response.json()["results"]

    def test_without_authentication(self):
        """
        Verify that trip listing is public - no authentication required.
        """
        response = self.client.get(self.url, {}, headers={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_trip_list_pagination(self):
        """
        Verify if the returned data has expected pagination keys
        """
        expected_keys = ["count", "results", "next", "previous"]
        response = self.client.get(self.url, {}, headers=self.headers)
        pagination_keys = response.json()
        self.assertTrue(
            all([expected_key in pagination_keys for expected_key in expected_keys]),
            pagination_keys,
        )

    def test_trip_list_results(self):
        """Verify if the returned data contains expected result keys"""
        expected_keys = [
            "name",
            "slug",
            "description",
            "duration",
            "country",
            "categories",
            "featured",
            "trip_url",
            "host",
        ]
        results = self.get_trips_list_result()
        self.assertEqual(len(results), 1)

        result_keys = results[0].keys()
        self.assertTrue(
            all([expected_key in result_keys for expected_key in expected_keys])
        )

    def test_filter_inactive_trips(self):
        """Verify inactive trips are not returned in api call"""
        TripFactory(is_active=False)
        trips = self.get_trips_list_result()
        self.assertEqual(len(trips), 1)

    @pytest.mark.skip(reason="Move this to trip detail")
    def test_api_trip_detail_data(self):
        def get_location_data(loc):
            return {
                "type": loc.get_type_display(),
                "name": loc.name,
                "slug": loc.slug,
                "travel_tips": loc.travel_tips,
                "lat": loc.lat,
                "lon": loc.lon,
                "importance": str(loc.importance),
                "is_active": loc.is_active,
            }

        trip_obj = self.trip
        trip_data = self.get_trips_list_result()[0]
        self.assertEqual(trip_data["name"], trip_obj.name)
        self.assertEqual(trip_data["slug"], trip_obj.slug)
        self.assertEqual(trip_data["description"], trip_obj.description)
        self.assertEqual(trip_data["duration"], str(trip_obj.duration))
        self.assertEqual(trip_data["overview"], trip_obj.overview)
        self.assertEqual(trip_data["included"], trip_obj.included)
        self.assertEqual(trip_data["excluded"], trip_obj.excluded)
        self.assertEqual(trip_data["add_ons"], trip_obj.add_ons)
        self.assertEqual(trip_data["travel_tips"], trip_obj.travel_tips)
        self.assertEqual(trip_data["requirements"], trip_obj.requirements)
        self.assertEqual(trip_data["child_policy"], trip_obj.child_policy)
        self.assertEqual(
            trip_data["facilities"],
            [
                {"id": ANY, "name": "Food", "slug": "food", "is_active": ANY},
                {"id": ANY, "name": "Transport", "slug": "transport", "is_active": ANY},
            ],
        )

        self.assertEqual(
            trip_data["gear"],
            [
                {"id": ANY, "name": "Backpack", "slug": "backpack", "is_active": ANY},
                {"id": ANY, "name": "Glasses", "slug": "glasses", "is_active": ANY},
            ],
        )

        self.assertEqual(trip_data["passenger_limit_min"], trip_obj.passenger_limit_min)
        self.assertEqual(trip_data["passenger_limit_max"], trip_obj.passenger_limit_max)
        self.assertEqual(trip_data["age_limit"], trip_obj.age_limit)

        # Location-related
        self.assertEqual(
            trip_data["departure"],
            get_location_data(trip_obj.departure),
        )
        self.assertEqual(
            trip_data["destination"], get_location_data(trip_obj.destination)
        )
        self.assertEqual(
            trip_data["locations"],
            [get_location_data(loc) for loc in trip_obj.locations.all()],
        )

        # Country
        self.assertEqual(trip_data["country"], "PK")

        # Categories
        self.assertEqual(
            trip_data["categories"],
            [
                {
                    "name": cat.name,
                    "slug": cat.slug,
                    "is_active": cat.is_active,
                }
                for cat in trip_obj.categories.all()
            ],
        )

        # Misc fields
        self.assertEqual(trip_data["metadata"], trip_obj.metadata)
        self.assertEqual(trip_data["featured"], trip_obj.featured)
        self.assertEqual(trip_data["is_pax_required"], trip_obj.is_pax_required)
        self.assertEqual(trip_data["is_active"], trip_obj.is_active)

        # Datetime fields
        self.assertIsNotNone(trip_data["created_at"])
        self.assertIsNotNone(trip_data["updated_at"])

        # Host info
        self.assertEqual(trip_data["host"]["name"], trip_obj.host.name)
        self.assertEqual(trip_data["host"]["slug"], trip_obj.host.slug)
        self.assertEqual(trip_data["host"]["description"], trip_obj.host.description)
        self.assertIsNotNone(trip_data["host"]["cancellation_policy"])
        self.assertIsNotNone(trip_data["host"]["verified"])
        self.assertIsNotNone(trip_data["host"]["type"])
        self.assertIsNotNone(trip_data["host"]["rating"])

        # Trip-specific
        self.assertEqual(trip_data["tags"], [])
        self.assertEqual(trip_data["trip_url"], trip_obj.get_absolute_url())

        # Remaining related fields
        self.assertIsNotNone(trip_data["trip_itinerary"])
        self.assertIsNotNone(trip_data["cancellation_policy"])


@ddt.ddt
@pytest.mark.django_db
class TestTripListFiltersAPI(AuthenticatedUserTestCase):
    """Covers the destination/duration/category/price/date filters and ordering on /trips/."""

    maxDiff = None
    url = reverse("trips-api:trip-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.hunza = LocationFactory(name="Hunza")
        cls.skardu = LocationFactory(name="Skardu")
        cls.hiking = CategoryFactory(name="Hiking")
        cls.honeymoon = CategoryFactory(name="Honeymoon")

        cls.trip_hunza = TripFactory(
            name="Hunza Adventure",
            destination=cls.hunza,
            duration=timedelta(days=5),
            categories=[cls.hiking],
        )
        cls.trip_skardu = TripFactory(
            name="Skardu Explorer",
            destination=cls.skardu,
            duration=timedelta(days=10),
            categories=[cls.honeymoon],
            host=HostFactory(verified=False),
        )

        cls.now = timezone.now().date()
        TripScheduleFactory(
            trip=cls.trip_hunza,
            price=15000,
            start_date=cls.now + timedelta(days=5),
            end_date=cls.now + timedelta(days=10),
            status=ScheduleStatus.PUBLISHED,
        )
        TripScheduleFactory(
            trip=cls.trip_skardu,
            price=30000,
            start_date=cls.now + timedelta(days=15),
            end_date=cls.now + timedelta(days=25),
            status=ScheduleStatus.PUBLISHED,
        )

    def get_results(self, params=None):
        response = self.client.get(self.url, params, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.json())
        return response.json()["results"]

    def test_filter_by_destination(self):
        """Previously broken/untested: field_name pointed at a non-existent `trip` relation."""
        data = self.get_results({"destination": self.hunza.slug})
        self.assertEqual({t["name"] for t in data}, {"Hunza Adventure"})

    def test_filter_by_duration_range(self):
        """Previously broken/untested: NumberFilter can't compare against a DurationField."""
        data = self.get_results({"duration_from": 8, "duration_to": 12})
        self.assertEqual({t["name"] for t in data}, {"Skardu Explorer"})

    def test_filter_by_category(self):
        data = self.get_results({"category": self.honeymoon.slug})
        self.assertEqual({t["name"] for t in data}, {"Skardu Explorer"})

    def test_filter_by_verified_host(self):
        data = self.get_results({"verified_host": "true"})
        self.assertEqual({t["name"] for t in data}, {"Hunza Adventure"})

    def test_filter_by_unverified_host(self):
        data = self.get_results({"verified_host": "false"})
        self.assertEqual({t["name"] for t in data}, {"Skardu Explorer"})

    def test_filter_by_price_range(self):
        data = self.get_results({"price_from": 20000})
        self.assertEqual({t["name"] for t in data}, {"Skardu Explorer"})

    def test_filter_by_date_from(self):
        data = self.get_results(
            {"date_from": (self.now + timedelta(days=14)).isoformat()}
        )
        self.assertEqual({t["name"] for t in data}, {"Skardu Explorer"})

    def test_ordering_by_price_ascending(self):
        data = self.get_results({"ordering": "price"})
        names = [t["name"] for t in data]
        self.assertEqual(names, ["Hunza Adventure", "Skardu Explorer"])

    def test_ordering_by_price_descending(self):
        data = self.get_results({"ordering": "-price"})
        names = [t["name"] for t in data]
        self.assertEqual(names, ["Skardu Explorer", "Hunza Adventure"])

    def test_no_duplicate_rows_from_multi_category_join(self):
        """A trip matching >1 filtered category shouldn't be duplicated by the join fan-out."""
        TripFactory(name="Multi Category Trip", categories=[self.hiking, self.honeymoon])
        data = self.get_results(
            {"category": f"{self.hiking.slug},{self.honeymoon.slug}"}
        )
        matched = [t for t in data if t["name"] == "Multi Category Trip"]
        self.assertEqual(len(matched), 1)

    def test_cross_schedule_conditions_must_be_satisfied_by_one_schedule(self):
        """
        A trip whose only cheap schedule is in the past and whose only future
        schedule is expensive should NOT match price_to=cheap & date_from=future,
        since no single schedule satisfies both constraints.
        """
        trip = TripFactory(name="Mismatched Schedule Trip", destination=self.hunza)
        TripScheduleFactory(
            trip=trip,
            price=5000,
            start_date=self.now - timedelta(days=30),
            end_date=self.now - timedelta(days=20),
            status=ScheduleStatus.PUBLISHED,
        )
        TripScheduleFactory(
            trip=trip,
            price=50000,
            start_date=self.now + timedelta(days=30),
            end_date=self.now + timedelta(days=40),
            status=ScheduleStatus.PUBLISHED,
        )
        data = self.get_results(
            {
                "price_to": 10000,
                "date_from": (self.now + timedelta(days=1)).isoformat(),
            }
        )
        self.assertNotIn("Mismatched Schedule Trip", {t["name"] for t in data})

    def test_empty_query_returns_all_active_trips(self):
        data = self.get_results()
        self.assertEqual(len(data), Trip.objects.active().count())
