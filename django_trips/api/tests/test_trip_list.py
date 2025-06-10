from datetime import timedelta
from unittest.mock import ANY

import ddt
import pytest
from django.urls import reverse
from django.utils import timezone

from django_trips.tests.factories import (
    TripFactory,
    TripScheduleFactory,
    AuthenticatedUserTestCase,
)


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
        Verify that we have access to all the data w/o authentication.
        """
        response = self.client.get(self.url, {}, headers={})
        self.assertEqual(response.status_code, 403)

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
            "is_featured",
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
        self.assertEqual(trip_data["is_featured"], trip_obj.is_featured)
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
