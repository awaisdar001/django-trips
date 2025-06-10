from datetime import timedelta
from unittest import mock

import ddt
from django.urls import reverse
from django.utils import timezone

from django_trips.choices import BookingStatus, ScheduleStatus
from django_trips.models import TripBooking
from django_trips.tests.factories import (AuthenticatedUserTestCase,
                                          TripBookingFactory, TripFactory,
                                          TripScheduleFactory)


class TripBookingCreateTestCase(AuthenticatedUserTestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.trip = TripFactory.create(
            locations=["Lahore", "Gilgit"],
            facilities=["Transport", "Food"],
            gear=["Backpack", "Glasses"],
            categories=["Outdoors", "Hiking"],
        )
        schedule_date = timezone.now().date() + timedelta(days=7)
        cls.trip_schedule = TripScheduleFactory(trip=cls.trip, start_date=schedule_date)
        cls.schedule2 = TripScheduleFactory(
            trip=cls.trip, start_date=timezone.now() + timedelta(days=20)
        )

        cls.url = reverse(
            "trips-api:trip-bookings-create", kwargs={"trip_id": cls.trip.pk}
        )
        cls.payload = {
            "schedule": cls.trip_schedule.id,
            "full_name": "Foo Bar",
            "email": "foo@bar.com",
            "phone_number": "+923331234567",
            "number_of_persons": 5,
            "target_date": schedule_date.isoformat(),
            "message": "this is a test message",
        }

    def make_create_trip_booking_request(self, data=None, expected_response=201):
        data = data or self.payload
        response = self.client.post(
            self.url, data, headers=self.headers, content_type="application/json"
        )
        self.assertEqual(response.status_code, expected_response, response.json())
        return response.json()

    def test_booking_create(self):
        data = self.make_create_trip_booking_request()
        self.assertTrue("number" in data)
        self.assertTrue("target_date" in data)
        new_booking = TripBooking.objects.get(number=data["number"])

        self.assertDictEqual(
            data,
            {
                "number": mock.ANY,
                "status": BookingStatus.PENDING,
                "full_name": "Foo Bar",
                "email": "foo@bar.com",
                "phone_number": "+923331234567",
                "number_of_persons": 5,
                "target_date": f"{new_booking.target_date.date().isoformat()}T00:00:00Z",
                "message": "this is a test message",
                "created_by": self.user.pk,
                "created": mock.ANY,
                "modified": mock.ANY,
                "schedule_details": mock.ANY,
            },
        )
