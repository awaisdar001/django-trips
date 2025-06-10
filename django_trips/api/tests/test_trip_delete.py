from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from django_trips.models import User, Trip
from django_trips.tests.factories import AuthenticatedUserTestCase, TripFactory


class TripDeletePermissionTests(AuthenticatedUserTestCase):
    def setUp(self):
        # Setup users
        self.staff_user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.trip = TripFactory()

        self.url = reverse(
            "trips-api:trip-detail", kwargs={"identifier": self.trip.slug}
        )

    def test_delete_as_staff(self):
        headers = self.get_access_token_header_for_user(self.staff_user)
        response = self.client.delete(self.url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify trip is deleted
        self.assertFalse(Trip.objects.filter(pk=self.trip.pk).exists())

    def test_delete_as_non_staff(self):
        response = self.client.delete(self.url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Verify trip still exists
        self.assertTrue(Trip.objects.filter(pk=self.trip.pk).exists())

    def test_delete_unauthenticated(self):
        response = self.client.delete(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )  # or 401 if auth required
        self.assertTrue(Trip.objects.filter(pk=self.trip.pk).exists())
