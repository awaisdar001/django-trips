from datetime import timedelta
from unittest import mock

import ddt
from django.urls import reverse
from django.utils import timezone

from django_trips.choices import BookingStatus, ScheduleStatus
from django_trips.models import TripBooking
from django_trips.tests.factories import (
    AuthenticatedUserTestCase,
    TripBookingFactory,
    TripFactory,
    TripScheduleFactory,
)


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
        cls.trip_schedule = TripScheduleFactory(
            trip=cls.trip,
            start_date=schedule_date,
            available_seats=20,
            booked_seats=0,
        )
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

    def test_booking_create_rejects_schedule_from_another_trip(self):
        other_trip = TripFactory.create(trip_schedule=None)
        other_schedule = TripScheduleFactory(trip=other_trip)

        data = self.make_create_trip_booking_request(
            {**self.payload, "schedule": other_schedule.id}, expected_response=400
        )
        self.assertIn("schedule", data)

    def test_booking_create_allows_anonymous_guest(self):
        response = self.client.post(
            self.url, self.payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, response.json())
        data = response.json()
        self.assertIsNone(data["created_by"])

        new_booking = TripBooking.objects.get(number=data["number"])
        self.assertIsNone(new_booking.created_by)

    def test_booking_create_increments_booked_seats(self):
        self.trip_schedule.refresh_from_db()
        before = self.trip_schedule.booked_seats

        self.make_create_trip_booking_request()

        self.trip_schedule.refresh_from_db()
        self.assertEqual(
            self.trip_schedule.booked_seats, before + self.payload["number_of_persons"]
        )

    def test_booking_create_rejects_when_not_enough_seats(self):
        self.trip_schedule.available_seats = 3
        self.trip_schedule.booked_seats = 0
        self.trip_schedule.save()

        data = self.make_create_trip_booking_request(
            {**self.payload, "number_of_persons": 5}, expected_response=400
        )
        self.assertIn("number_of_persons", data)

        self.trip_schedule.refresh_from_db()
        self.assertEqual(self.trip_schedule.booked_seats, 0)
