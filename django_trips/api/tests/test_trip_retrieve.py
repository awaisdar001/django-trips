from django.urls import reverse
from rest_framework import status

from django_trips.tests.factories import (AuthenticatedUserTestCase,
                                          CategoryFactory, FacilityFactory,
                                          GearFactory, HostFactory,
                                          LocationFactory, TripFactory,
                                          TripItineraryFactory,
                                          TripOptionFactory)


class TripRetrieveTestCase(AuthenticatedUserTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.trip = TripFactory(
            locations=["Lahore", "Gilgit"],
            facilities=["Transport", "Food"],
            gear=["Backpack", "Glasses"],
            categories=["Outdoors", "Hiking"],
        )
        cls.option1 = TripOptionFactory(trip=cls.trip, name="Deluxe")
        cls.option2 = TripOptionFactory(trip=cls.trip, name="Budget")
        cls.option3 = TripOptionFactory(trip=cls.trip, name="Five Star")
        cls.host = cls.trip.host
        cls.destination = cls.trip.destination
        cls.departure = cls.trip.departure
        cls.trip.locations.add(cls.departure, cls.destination)

        # Add itinerary
        TripItineraryFactory(
            trip=cls.trip,
            day_index=1,
            title="Arrival Day",
            location=cls.departure,
            category=cls.trip.categories.all().first(),
        )

    def make_api_call(self, identifier, expected_status_code=status.HTTP_200_OK):
        url = reverse("trips-api:trip-detail", kwargs={"identifier": identifier})
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, expected_status_code)
        return response.json()

    def test_retrieve_trip_by_id(self):
        data = self.make_api_call(self.trip.id)
        self.assertEqual(data["id"], self.trip.id)
        self.assertEqual(data["name"], self.trip.name)

    def test_retrieve_trip_by_slug(self):
        data = self.make_api_call(self.trip.slug)
        self.assertEqual(data["slug"], self.trip.slug)

    def test_trip_detail_serializer_fields_present(self):
        data = self.make_api_call(self.trip.slug)
        expected_fields = {
            "id",
            "name",
            "slug",
            "description",
            "duration",
            "host",
            "departure",
            "destination",
            "facilities",
            "gear",
            "categories",
            "locations",
            "trip_itinerary",
            "tags",
            "options",
        }
        self.assertTrue(expected_fields.issubset(data.keys()))

    def test_retrieve_nonexistent_trip_returns_404(self):
        self.make_api_call("non-existent-slug", status.HTTP_404_NOT_FOUND)
