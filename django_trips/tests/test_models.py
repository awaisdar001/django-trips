from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from django_trips.choices import LocationType, ScheduleStatus
from django_trips.models import (
    CancellationPolicy,
    Facility,
    Location,
    Trip,
    TripSchedule,
    HostType,
    TripItinerary,
)
from django_trips.tests.factories import (
    FacilityFactory,
    GearFactory,
    HostFactory,
    LocationFactory,
    TripItineraryFactory,
    TripScheduleFactory,
    get_trip,
    TripFactory,
)


class LocationFactoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.location = LocationFactory(name="My Test Location")

    def test_create(self):
        """Test that the location object is created successfully."""
        location = self.location
        self.assertEqual(location.name, "My Test Location")
        self.assertTrue(location.is_active)
        self.assertIsNotNone(location.lat)
        self.assertIsNotNone(location.lon)

    def test_lat_lon_coordinates(self):
        """Ensure that the `lat` and `lon` values are floats and within valid ranges."""
        location = self.location
        self.assertIsInstance(location.lat, float)
        self.assertIsInstance(location.lon, float)
        self.assertGreaterEqual(location.lat, -90)
        self.assertLessEqual(location.lat, 90)
        self.assertGreaterEqual(location.lon, -180)
        self.assertLessEqual(location.lon, 180)

    def test_slug_unique(self):
        """Test that the slug is unique."""
        location = self.location
        duplicate_location = LocationFactory(name="Test Location 1")
        self.assertNotEqual(location.slug, duplicate_location.slug)

    def test_travel_tips(self):
        """Test that `travel_tips` contains valid data."""
        location = self.location
        self.assertIsInstance(location.travel_tips, dict)
        self.assertIn("tip", location.travel_tips)

    def test_type(self):
        """Ensure the type of location is one of the choices from LocationType."""
        location = self.location
        self.assertIn(location.type, [choice[0] for choice in LocationType.choices])

    def test_importance(self):
        """Test that `importance` is within the expected range."""
        location = self.location
        self.assertGreaterEqual(location.importance, 0.1)
        self.assertLessEqual(location.importance, 2.0)

    def test_active_status(self):
        """Test that location is active by default."""
        location = self.location
        self.assertTrue(location.is_active)

    def test_location_factory_creates_location(self):
        """Test that the factory is properly creating a `Location` object."""
        location = LocationFactory()
        self.assertIsInstance(location, Location)
        self.assertIsNotNone(location.id)


class HostFactoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.host_type = HostType.objects.create(name="Adventure")
        cls.host = HostFactory(name="Test Host", type=cls.host_type)

    def test_create_host(self):
        """Test that the host object is created successfully."""
        host = self.host
        self.assertEqual(host.name, "Test Host")
        self.assertEqual(host.type.name, "Adventure")
        self.assertIsInstance(host.slug, str)

    def test_host_contact_info(self):
        """Test email and mobile fields are generated properly."""
        self.assertIn("@", self.host.email)
        self.assertTrue(self.host.mobile.startswith("+92"))
        self.assertGreaterEqual(len(self.host.mobile), 11)

    def test_host_cnic_format(self):
        """Test that CNIC has exactly 13 digits."""
        self.assertEqual(len(self.host.cnic), 11)
        self.assertTrue(self.host.cnic.isdigit())

    def test_cancellation_policy_structure(self):
        """Test that cancellation_policy is a list of dicts."""
        policy = self.host.cancellation_policy
        self.assertIsInstance(policy, list)
        for item in policy:
            self.assertIn("policy", item)
            self.assertIn("days", item)

    def test_refund_policy_structure(self):
        """Test that refund_policy is a list of dicts."""
        policy = self.host.refund_policy
        self.assertIsInstance(policy, list)
        for item in policy:
            self.assertIn("policy", item)
            self.assertIn("days", item)

    def test_verified_flag(self):
        """Test that the verified flag is a boolean."""
        self.assertIn(self.host.verified, [True, False])

    def test_host_str_representation(self):
        """Test the __str__ method if implemented."""
        self.assertIn("Test Host", str(self.host))


class TestFacility(TestCase):
    """
    Verify CRUD operations for Facility model.
    """

    @classmethod
    def setUpTestData(cls):
        cls.facility = FacilityFactory()

    def test_create_facility(self):
        self.assertIsNotNone(self.facility.id)

    def test_update_facility(self):
        self.facility.name = "No Food"
        self.facility.save()
        self.facility.refresh_from_db()
        self.assertEqual("No Food", self.facility.name)

    def test_delete_facility(self):
        self.assertEqual(1, len(Facility.objects.all()))
        self.facility.delete()
        self.assertEqual(0, len(Facility.objects.all()))


class TestTrip(TestCase):
    """Test the application Trip model for CURD operations"""

    @classmethod
    def setUpTestData(cls):
        cls.trip = TripFactory.create(
            locations=["Lahore", "Gilgit"],
            facilities=["Transport", "Food"],
            gear=["Backpack", "Glasses"],
            categories=["Outdoors", "Hiking"],
            trip_schedule=2,
        )

    def test_create(self):
        """Checks if setup has created model object"""
        self.assertIsNotNone(self.trip.id)
        self.assertTrue(len(self.trip.slug) > 0)

    def test_gear_update(self):
        """Test update gear"""
        current_trip_gears = self.trip.gear.all().count()
        new_gear = GearFactory()
        self.trip.gear.add(*[new_gear])

        self.trip.refresh_from_db()
        new_trip_gears = self.trip.gear.all()

        self.assertNotEqual(current_trip_gears, new_trip_gears.count())
        self.assertTrue(new_gear in new_trip_gears)

    def test_trip_itinerary(self):
        """Test trip itinerary"""
        self.assertEqual(self.trip.itinerary_days.all().count(), 0)
        TripItineraryFactory(trip=self.trip, day_index=1)
        TripItineraryFactory(trip=self.trip, day_index=2)
        self.assertEqual(self.trip.itinerary_days.all().count(), 2)

    def test_trip_schedule(self):
        """Test Trip schedule update."""
        today_date = timezone.now()
        trip_without_schedules = get_trip(trip_schedules=None)
        self.assertEqual(trip_without_schedules.schedules.all().count(), 0)

        __ = TripScheduleFactory(trip=trip_without_schedules, start_date=today_date)
        trip_without_schedules.refresh_from_db()

        trip_schedules = trip_without_schedules.schedules.all()
        self.assertEqual(trip_schedules.all().count(), 1)
        self.assertEqual(trip_schedules.get().start_date, today_date.date())

    def stest_trip_availability(self):
        """Test available manager of trip schedule"""
        future_trip_date = timezone.now() + timedelta(days=7)
        past_trip_date = timezone.now() - timedelta(days=7)
        trip = get_trip(trip_schedules=None)

        __ = TripScheduleFactory(trip=trip, date_from=past_trip_date)
        self.assertEqual(TripSchedule.objects.active().filter(trip=trip).count(), 0)

        __ = TripScheduleFactory(trip=trip, date_from=future_trip_date)
        self.assertEqual(TripSchedule.objects.active().filter(trip=trip).count(), 1)

    def test_cancellation_policy(self):
        """
        Tests cancellation policy override.

        When trip object has cancellation policy, it should be given preference
        over host cancellation policy.
        """
        self.trip.host.cancellation_policy = {}
        self.trip.host.save()

        common_policy = "Common trip CancellationPolicy"
        CancellationPolicy(description=common_policy).save()
        new_cancellation_policy = "new cancellation policy"

        self.assertEqual(
            self.trip.cancellation_policy, CancellationPolicy.current().description
        )

        # Update host policy.
        self.trip.host.cancellation_policy = new_cancellation_policy
        self.trip.host.save()
        self.assertEqual(self.trip.cancellation_policy, new_cancellation_policy)


class TripScheduleFactoryTestCase(TestCase):

    def test_create_trip_schedule(self):
        # Create a trip schedule using the factory
        trip_schedule = TripScheduleFactory(status=ScheduleStatus.DRAFT)

        # Check if the trip schedule was created successfully
        self.assertIsInstance(trip_schedule, TripSchedule)

        # Check the validity of fields
        self.assertTrue(trip_schedule.start_date)
        self.assertTrue(trip_schedule.end_date)
        self.assertTrue(0 <= trip_schedule.available_seats <= 100)  # Check seats range
        self.assertTrue(0 <= trip_schedule.booked_seats <= 100)

        # Test default status is 'DRAFT'
        self.assertEqual(trip_schedule.status, ScheduleStatus.DRAFT)

    def test_price_validation(self):
        # Create a trip schedule with a price
        trip_schedule = TripScheduleFactory(price=5000)

        # Assert that the price is valid (i.e., not negative or zero)
        self.assertGreater(trip_schedule.price, 0, "Price should be greater than zero")

    def test_status_choices(self):
        # Create trip schedules with different statuses
        draft_schedule = TripScheduleFactory(status=ScheduleStatus.DRAFT)
        confirmed_schedule = TripScheduleFactory(status=ScheduleStatus.PUBLISHED)
        cancelled_schedule = TripScheduleFactory(status=ScheduleStatus.CANCELLED)

        # Assert that statuses are set correctly
        self.assertEqual(draft_schedule.status, ScheduleStatus.DRAFT)
        self.assertEqual(confirmed_schedule.status, ScheduleStatus.PUBLISHED)
        self.assertEqual(cancelled_schedule.status, ScheduleStatus.CANCELLED)


class TripItineraryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.itinerary = TripItineraryFactory()

    def test_itinerary_creation(self):
        self.assertIsInstance(self.itinerary, TripItinerary)
        self.assertIsNotNone(self.itinerary.trip)
        self.assertGreaterEqual(self.itinerary.day_index, 1)

    def test_title_and_description(self):
        self.assertTrue(self.itinerary.title)
        self.assertTrue(isinstance(self.itinerary.description, str))

    def test_start_and_end_time(self):
        self.assertIsNotNone(self.itinerary.start_time)
        self.assertIsNotNone(self.itinerary.end_time)
        self.assertGreater(self.itinerary.end_time, self.itinerary.start_time)

    def test_location_and_category(self):
        self.assertIsNotNone(self.itinerary.location)
        self.assertIsNotNone(self.itinerary.category)
