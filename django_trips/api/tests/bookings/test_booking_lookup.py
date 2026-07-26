from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from django_trips.tests.factories import TripBookingFactory, TripFactory, TripScheduleFactory


class TripBookingLookupTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.trip = TripFactory()
        cls.schedule_date = timezone.now().date() + timedelta(days=7)
        cls.trip_schedule = TripScheduleFactory(
            trip=cls.trip, start_date=cls.schedule_date
        )
        cls.booking = TripBookingFactory(
            schedule=cls.trip_schedule,
            full_name="Ali Raza",
            email="ali@example.com",
            number="DPT00123AA",
            target_date=cls.schedule_date,
            created_by=None,
        )
        cls.url = reverse("trips-api:trip-bookings-lookup")

    def test_lookup_by_number_and_email(self):
        response = self.client.get(
            self.url, {"number": self.booking.number, "email": "ali@example.com"}
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["number"], self.booking.number)

    def test_lookup_is_case_insensitive_on_email(self):
        response = self.client.get(
            self.url, {"number": self.booking.number, "email": "ALI@EXAMPLE.COM"}
        )
        self.assertEqual(response.status_code, 200, response.json())

    def test_lookup_rejects_mismatched_email(self):
        response = self.client.get(
            self.url,
            {"number": self.booking.number, "email": "someone-else@example.com"},
        )
        self.assertEqual(response.status_code, 404)

    def test_lookup_requires_both_params(self):
        response = self.client.get(self.url, {"number": self.booking.number})
        self.assertEqual(response.status_code, 400)

        response = self.client.get(self.url, {"email": "ali@example.com"})
        self.assertEqual(response.status_code, 400)
