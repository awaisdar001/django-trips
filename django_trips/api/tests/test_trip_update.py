from unittest.mock import ANY

from django.test import TestCase
from django.urls import reverse

from django_trips.tests import factories
from django_trips.tests.factories import (AuthenticatedUserTestCase,
                                          CategoryFactory, FacilityFactory,
                                          GearFactory, HostFactory,
                                          LocationFactory, TripFactory,
                                          TripItineraryFactory, UserFactory)


class TripUpdateTestCase(AuthenticatedUserTestCase):
    maxDiff = None

    @property
    def url(self):
        return reverse("trips-api:trip-detail", kwargs={"identifier": self.trip.id})

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.trip = TripFactory(
            locations=["Lahore", "Gilgit"],
            facilities=["Transport", "Food"],
            gear=["Backpack", "Glasses"],
            categories=["Outdoors", "Hiking"],
        )
        cls.host = cls.trip.host
        cls.destination = cls.trip.destination
        cls.departure = cls.trip.departure
        cls.gear1, cls.gear2 = cls.trip.gear.all()
        cls.facility1, cls.facility2 = cls.trip.facilities.all()
        cls.category = cls.trip.categories.all().first()
        cls.trip.locations.add(cls.departure, cls.destination)

        # Add itinerary
        TripItineraryFactory(
            trip=cls.trip,
            day_index=1,
            title="Arrival Day",
            location=cls.departure,
            category=cls.category,
        )

    def setUp(self):
        self.payload = {
            "name": "Updated Trip Name",
            "slug": "updated-trip-slug",
            "description": "New Description",
            "duration": "6 00:00:00",
            "departure": self.departure.id,
            "destination": self.destination.id,
            "locations": [self.departure.id, self.destination.id],
            "facilities": [self.facility1.id, self.facility2.id],
            "gear": [self.gear1.id, self.gear2.id],
            "categories": [self.category.id],
            "host": self.host.id,
            "tags": ["updated", "trip"],
            "trip_itinerary": [
                {
                    "day": 1,
                    "title": "Updated Day",
                    "description": "Updated Description",
                    "location": self.departure.id,
                    "category": self.category.id,
                    "start_time": "2025-06-02T08:00:00Z",
                    "end_time": "2025-06-02T20:00:00Z",
                }
            ],
        }
        self.payload_with_itinerary = {
            **self.payload,
            "trip_itinerary": [
                {
                    "day": 1,
                    "title": "New Arrival",
                    "description": "Arrive and relax (New).",
                    "location": self.departure.id,
                    "category": self.category.id,
                    "start_time": "2025-06-01T08:00:00Z",
                    "end_time": "2025-06-01T20:00:00Z",
                }
            ],
        }

    def make_update_trip_request(self, data=None, expected_response=200):
        data = data if data is not None else self.payload
        response = self.client.put(
            self.url, data, headers=self.headers, content_type="application/json"
        )
        self.assertEqual(response.status_code, expected_response, response.json())
        return response.json()

    def test_basic_trip_update(self):
        data = self.make_update_trip_request()
        self.assertEqual(data["name"], self.payload["name"])

    def test_trip_update_with_itinerary(self):
        data = self.make_update_trip_request(self.payload_with_itinerary)
        trip_itinerary = data["trip_itinerary"]
        self.assertEqual(len(trip_itinerary), 1, data)
        itinerary = trip_itinerary[0]
        self.assertEqual(itinerary["title"], "New Arrival")
        self.assertEqual(itinerary["description"], "Arrive and relax (New).")

    def test_trip_update_with_itinerary_related_fields(self):
        data = self.make_update_trip_request(self.payload_with_itinerary)

        self.assertEqual(len(data["trip_itinerary"]), 1, data)
        trip_itinerary = data["trip_itinerary"][0]
        self.assertEqual(trip_itinerary["day"], 1)

        self.assertDictEqual(
            trip_itinerary["location"],
            {
                "type": self.departure.get_type_display(),
                "name": self.departure.name,
                "slug": self.departure.slug,
                "travel_tips": ANY,
                "lat": ANY,
                "lon": ANY,
                "importance": ANY,
            },
        )
        self.assertEqual(
            trip_itinerary["category"],
            {"name": self.category.name, "slug": ANY},
        )

    def test_trip_update_missing_required_field(self):
        payload = {"slug": "missing-name"}  # Missing 'name'
        data = self.make_update_trip_request(payload, 400)
        self.assertIn("name", data)

    def test_invalid_departure_location(self):
        payload = {
            # ... basic valid data ...
            "departure": 99999,  # Non-existent
            "destination": self.destination.id,
            # other required fields...
        }
        data = self.make_update_trip_request(payload, 400)
        self.assertIn("departure", data)

    def test_trip_update_invalid_gear(self):
        data = {"gear": [9999]}  # Non-existent gear ID
        self.make_update_trip_request(data, 400)

    def test_trip_update_empty_payload(self):
        self.make_update_trip_request({}, 400)
