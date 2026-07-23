from django.test import TestCase
from rest_framework import serializers

from django_trips.api.serializers import HostSerializer, TripCreateSerializer
from django_trips.models import HostRating
from django_trips.tests.factories import HostFactory


class HostSerializerRatingTestCase(TestCase):
    def test_rating_defaults_to_zero_without_host_rating(self):
        host = HostFactory()
        data = HostSerializer(host).data
        self.assertEqual(data["rating"], {"rating_count": 0, "rated_by": 0})

    def test_rating_reflects_host_rating_when_present(self):
        host = HostFactory()
        HostRating.objects.create(host=host, rating_count=25, rated_by=5)
        data = HostSerializer(host).data
        self.assertEqual(data["rating"], {"rating_count": 25, "rated_by": 5})


class TripCreateSerializerValidateTestCase(TestCase):
    def test_raises_for_empty_body(self):
        with self.assertRaises(serializers.ValidationError):
            TripCreateSerializer().validate({})
