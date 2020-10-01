# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase
from pytz import UTC

from trips.models import (
    Facility,
    Host,
    Location,
    Trip,
    TripSchedule,
    CancellationPolicy,
)
from trips.tests.factories import (
    ActivityFactory,
    FacilityFactory,
    HostFactory,
    LocationFactory,
    TripFactory,
    TripItineraryFactory,
    TripScheduleFactory,
)


class TestHost(TestCase):
    """
    Test Suite for verifying various operations on Host model.
    """

    def setUp(self):
        self.host = HostFactory()

    def test_create_host(self):
        """
        Test that Host object creates successfully with required
        and optional fields.
        """
        # Successful Save will create id
        self.assertIsNotNone(self.host.id)
        self.assertIsNone(self.host.description)
        self.assertFalse(self.host.verified)

        # Adding Optional Fields
        self.host.description = "Travel Company"
        self.host.verified = True
        self.host.save()
        self.assertEqual(self.host.verified, True)
        self.assertIsNotNone(self.host.description)

    def test_update_host(self):
        """
        Test that updating the Host object works with changes
        reflected after the save
        """
        prev_description = self.host.description
        self.host.verified = True
        self.host.description = "Software Company"
        self.host.save()
        updated_host = Host.objects.filter(name=self.host.name)[0]
        self.assertNotEqual(prev_description, updated_host.description)

    def test_delete_host(self):
        """
        Test deleting an object works and object is not
        accessible after deletion
        """
        host_name = self.host.name
        self.host.delete()
        with self.assertRaises(Host.DoesNotExist):
            Host.objects.get(name=host_name)


class TestLocation(TestCase):
    """
    Test Suite to verify Location model w.r.t CRUD Operations.
    """

    def setUp(self):
        self.location = LocationFactory()

    def test_create_location(self):
        """
        Test location object is created successfully after save
        """
        self.assertIsNotNone(self.location.id)

    def test_update_location(self):
        """
        Test location objects are persisted after update.
        """
        self.assertIsNone(self.location.coordinates)
        self.location.coordinates = "-95, 45"
        self.location.save()
        updated_location = Location.objects.filter(name=self.location.name)[0]
        self.assertIsNotNone(updated_location.coordinates)

    def test_delete_location(self):
        """
        Test location objects are no longer persisted after delete.
        """
        location_name = self.location.name
        self.location.delete()
        with self.assertRaises(Location.DoesNotExist):
            Location.objects.get(name=location_name)


class TestFacility(TestCase):
    """
    Verify CRUD operations for Facility model.
    """

    def setUp(self):
        self.facility = FacilityFactory()

    def test_create_facility(self):
        """
        Test facility is created successfully after save operation.
        """
        self.assertIsNotNone(self.facility.id)

    def test_update_facility(self):
        """
        Test facility object updates are persisted successfully after save.
        """
        id = self.facility.id
        self.facility.name = "No Food"
        self.facility.save()
        updated_facility = Facility.objects.filter(id=id)[0]
        self.assertEqual("No Food", updated_facility.name)

    def test_delete_facility(self):
        """
        Test the facility object is not longer persisted after delete.
        """
        self.assertEqual(1, len(Facility.objects.all()))
        self.facility.delete()
        self.assertEqual(0, len(Facility.objects.all()))


class TestTrip(TestCase):
    """Test the application Trip model for CURD oprations"""

    def setUp(self):
        """Setup objects for testing"""
        self.trip = TripFactory.create(locations=["Lahore", "Gilgit"])

    def _update_trip_field(self, field, value):
        """Updates a field in trip object"""
        setattr(self.trip, field, value)
        self.trip.save()

    def test_create(self):
        """Checks if setup has created model object"""
        self.assertIsNotNone(self.trip.id)

    def test_update(self):
        """Test update trip method."""
        new_description = u"This is my dummy description"
        self._update_trip_field("description", new_description)

        trip = Trip.objects.get(id=self.trip.id)
        self.assertEqual(new_description, trip.description)

    def test_delete(self):
        """Test Trip delete"""
        self.assertEqual(Trip.objects.all().count(), 1)
        self.trip.delete()
        self.assertEqual(Trip.objects.all().count(), 0)

    def test_gear_update(self):
        """Test update gear"""
        new_gear = u"My test gear"
        self._update_trip_field("gear", new_gear)
        self.assertEqual(Trip.objects.get(id=self.trip.id).gear, new_gear)

    def test_trip_itinerary(self):
        """Test trip itinerary"""
        self.assertEqual(self.trip.trip_itinerary.all().count(), 0)
        TripItineraryFactory(trip=self.trip, day=1)
        TripItineraryFactory(trip=self.trip, day=2)
        self.assertEqual(self.trip.trip_itinerary.all().count(), 2)

    def test_trip_schedule(self):
        """Test Trip schedule"""
        today_date = datetime.now(tz=UTC)
        self.assertEqual(self.trip.trip_schedule.all().count(), 0)
        __ = TripScheduleFactory(trip=self.trip, date_from=today_date)
        trip_schedules = self.trip.trip_schedule.all()
        self.assertEqual(trip_schedules.all().count(), 1)
        self.assertEqual(trip_schedules.get().date_from, today_date)

    def test_trip_availability(self):
        """Test available manager of trip schedule"""
        future_trip_date = timezone.now() + timedelta(days=7)
        past_trip_date = timezone.now() - timedelta(days=7)
        past_trip = TripScheduleFactory(trip=self.trip, date_from=past_trip_date)

        __ = TripScheduleFactory(trip=self.trip)
        self.assertEqual(TripSchedule.available.all().count(), 0)
        __ = TripScheduleFactory(trip=self.trip, date_from=future_trip_date)
        self.assertEqual(TripSchedule.available.all().count(), 1)
        self.assertEqual(TripSchedule.objects.all().count(), 2)

    def test_cancellation_policy(self):
        """
        Tests cancellation policy override.

        When trip object has cancellation policy, it should be given perfernce
        over host cancellation policy.
        """
        self.trip.host.cancellation_policy = None
        self.trip.host.save()

        common_policy = "Common trip CancellationPolicy"
        CancellationPolicy(description=common_policy).save()
        new_cancellation_policy = "new cancellation policy"

        self.assertEqual(self.trip.cancellation_policy, CancellationPolicy.current().description)

        # Update host policy.
        self.trip.host.cancellation_policy = new_cancellation_policy
        self.trip.host.save()
        self.assertEqual(self.trip.cancellation_policy, new_cancellation_policy)
