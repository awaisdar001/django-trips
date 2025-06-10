from unittest.mock import ANY

from django.urls import reverse

from django_trips.tests.factories import (
    HostFactory,
    LocationFactory,
    FacilityFactory,
    GearFactory,
    CategoryFactory,
    AuthenticatedUserTestCase,
)


class TripCreateTestCase(AuthenticatedUserTestCase):
    maxDiff = None
    url = reverse("trips-api:trip-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.host = HostFactory()
        cls.departure = LocationFactory()
        cls.destination = LocationFactory()
        cls.facility = FacilityFactory()
        cls.gear1 = GearFactory()
        cls.gear2 = GearFactory()
        cls.category = CategoryFactory()

        cls.payload = {
            "name": "Trip to Skardu",
            "slug": "trip-to-skardu",
            "description": "A basic test trip",
            "duration": "5 00:00:00",
            "departure": cls.departure.id,
            "destination": cls.destination.id,
            "locations": [cls.departure.id, cls.destination.id],
            "facilities": [cls.facility.id],
            "gear": [cls.gear1.id, cls.gear2.id],
            "categories": [cls.category.id],
            "host": cls.host.id,
            "tags": ["adventure", "nature"],
        }

        cls.payload_with_itinerary = {
            **cls.payload,
            "trip_itinerary": [
                {
                    "day": 1,
                    "title": "Arrival",
                    "description": "Arrive and relax.",
                    "location": cls.departure.id,
                    "category": cls.category.id,
                    "start_time": "2025-06-01T08:00:00Z",
                    "end_time": "2025-06-01T20:00:00Z",
                }
            ],
        }

    def make_create_trip_request(self, data=None, expected_response=201):
        data = data or self.payload
        response = self.client.post(
            self.url, data, headers=self.headers, content_type="application/json"
        )
        self.assertEqual(response.status_code, expected_response, response.json())
        return response.json()

    def test_basic_trip_create(self):
        data = self.make_create_trip_request()
        self.assertEqual(data["name"], self.payload["name"])

    def test_trip_create_with_itinerary(self):
        data = self.make_create_trip_request(self.payload_with_itinerary)
        self.assertEqual(len(data["trip_itinerary"]), 1, data)

    def test_trip_create_with_itinerary_response(self):
        data = self.make_create_trip_request(self.payload_with_itinerary)

        self.assertEqual(len(data["trip_itinerary"]), 1, data)
        trip_itinerary = data["trip_itinerary"][0]
        self.assertEqual(trip_itinerary["day"], 1)
        self.assertEqual(trip_itinerary["title"], "Arrival")
        self.assertEqual(trip_itinerary["description"], "Arrive and relax.")

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

    def test_trip_create_missing_required_field(self):
        payload = {"slug": "missing-name"}  # Missing 'name'
        data = self.make_create_trip_request(payload, 400)
        self.assertIn("name", data)

    def test_invalid_departure_location(self):
        payload = {
            # ... basic valid data ...
            "departure": 99999,  # Non-existent
            "destination": self.destination.id,
            # other required fields...
        }
        data = self.make_create_trip_request(payload, 400)
        self.assertIn("departure", data)
