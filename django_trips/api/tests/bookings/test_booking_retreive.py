from datetime import timedelta
from unittest import mock

from django.urls import reverse
from django.utils import timezone

from django_trips.models import TripBooking
from django_trips.tests.factories import (AuthenticatedUserTestCase,
                                          TripBookingFactory, TripFactory,
                                          TripScheduleFactory)


class TripCreateBookingTestCase(AuthenticatedUserTestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.trip = TripFactory()
        cls.schedule_date = timezone.now().date() + timedelta(days=7)
        cls.trip_schedule = TripScheduleFactory(
            trip=cls.trip, start_date=cls.schedule_date
        )
        cls.booking1 = TripBookingFactory(
            schedule=cls.trip_schedule,
            full_name="Ali Raza",
            phone_number="03001234567",
            number="DPT00123AA",
            target_date=cls.schedule_date,
            number_of_persons=5,
            message="booking 1",
            created_by=cls.user,
        )
        cls.booking2 = TripBookingFactory(
            schedule=cls.trip_schedule,
            full_name="Sara Khan",
            phone_number="03111234567",
            number="DPT00124BB",
            target_date=cls.schedule_date,
            number_of_persons=10,
            message="booking 2",
        )
        cls.url = reverse(
            "trips-api:booking-detail", kwargs={"number": cls.booking1.number}
        )

    def test_trip_retrieve(self):
        response = self.client.get(self.url, headers=self.headers)
        assert response.status_code == 200
        self.assertDictEqual(
            response.json(),
            {
                "number": self.booking1.number,
                "status": "PENDING",
                "full_name": "Ali Raza",
                "email": self.booking1.email,
                "phone_number": "03001234567",
                "number_of_persons": 5,
                "target_date": f"{self.schedule_date.isoformat()}T00:00:00Z",
                "message": "booking 1",
                "created": mock.ANY,
                "modified": mock.ANY,
                "schedule_details": mock.ANY,
                "created_by": self.user.pk,
            },
        )
