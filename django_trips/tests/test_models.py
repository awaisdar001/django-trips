from datetime import timedelta

from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from django_trips.choices import AvailabilityType, LocationType, ScheduleStatus
from django_trips.models import (
    CancellationPolicy,
    Facility,
    Host,
    HostRating,
    HostType,
    Location,
    RefundPolicy,
    Testimonial,
    TripAvailability,
    TripBooking,
    TripItinerary,
    TripPickupLocation,
    TripReview,
    TripSchedule,
    TripWishlist,
    TrustBadge,
)
from django_trips.tests.factories import (
    CategoryFactory,
    FacilityFactory,
    GearFactory,
    HostFactory,
    HostTypeFactory,
    LocationFactory,
    TestimonialFactory,
    TripBookingFactory,
    TripFactory,
    TripImageFactory,
    TripItineraryFactory,
    TripOptionFactory,
    TripReviewFactory,
    TripReviewSummaryFactory,
    TripScheduleFactory,
    TripWishlistFactory,
    UserFactory,
    get_trip,
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

    def test_region_from_parent(self):
        """A location with a parent should report the parent's name as its region."""
        province = LocationFactory(name="Gilgit-Baltistan", type=LocationType.PROVINCE)
        town = LocationFactory(name="Hunza", type=LocationType.TOWN, parent=province)
        self.assertEqual(town.region, "Gilgit-Baltistan")

    def test_region_for_province_without_parent(self):
        """A PROVINCE-level location with no parent should report its own name."""
        province = LocationFactory(name="Sindh", type=LocationType.PROVINCE, parent=None)
        self.assertEqual(province.region, "Sindh")

    def test_region_none_when_unlinked(self):
        """A non-PROVINCE location with no parent set yet has no region."""
        town = LocationFactory(type=LocationType.TOWN, parent=None)
        self.assertIsNone(town.region)

    def test_repr(self):
        self.assertIn(self.location.name, repr(self.location))


class SlugMixinTestCase(TestCase):
    """SlugMixin.save() (django_trips/mixins.py) auto-generates a unique slug,
    appending a numeric suffix on collision."""

    def test_appends_numeric_suffix_on_slug_collision(self):
        first = Location.objects.create(name="Hunza Valley")
        second = Location.objects.create(name="Hunza Valley")
        third = Location.objects.create(name="Hunza Valley")

        self.assertEqual(first.slug, "hunza-valley")
        self.assertEqual(second.slug, "hunza-valley-2")
        self.assertEqual(third.slug, "hunza-valley-3")


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

    def test_host_repr_representation(self):
        self.assertIn("Test Host", repr(self.host))


class HostTypeTestCase(TestCase):
    def test_str_and_repr(self):
        host_type = HostTypeFactory(name="Adventure Tours")
        self.assertEqual(str(host_type), "Adventure Tours")
        self.assertIn("Adventure Tours", repr(host_type))


class HostRatingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.host = HostFactory()

    def test_str_and_repr(self):
        rating = HostRating.objects.create(host=self.host, rating_count=10, rated_by=5)
        self.assertIn(str(rating.rating_count), str(rating))
        self.assertIn("HostRating", repr(rating))


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

    def test_str(self):
        self.assertEqual(str(self.facility), self.facility.name)

    def test_repr(self):
        self.assertIn(self.facility.name, repr(self.facility))


class LookupModelStrReprTestCase(TestCase):
    """__str__/__repr__ for the remaining simple M2M lookup-style models."""

    def test_gear(self):
        gear = GearFactory(name="Compass")
        self.assertEqual(str(gear), "Compass")
        self.assertIn("Compass", repr(gear))

    def test_category(self):
        category = CategoryFactory(name="Hiking")
        self.assertEqual(str(category), "Hiking")
        self.assertIn("Hiking", repr(category))

    def test_trust_badge(self):
        badge = TrustBadge.objects.create(name="Certified Guide", slug="certified-guide")
        self.assertEqual(str(badge), "Certified Guide")
        self.assertIn("Certified Guide", repr(badge))


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

    def test_trip_images_ordering(self):
        """Images should come back ordered by `order`, regardless of creation order."""
        second = TripImageFactory(trip=self.trip, order=2)
        first = TripImageFactory(trip=self.trip, order=1)
        third = TripImageFactory(trip=self.trip, order=3)

        self.assertEqual(list(self.trip.images.all()), [first, second, third])

    def test_poster_prefers_first_trip_image_over_metadata(self):
        """Trip.poster should use the first TripImage (by order) when one exists."""
        trip = TripFactory(
            metadata={"poster": "https://example.com/legacy-poster.jpg"},
            trip_schedule=None,
        )
        TripImageFactory(trip=trip, order=2, image="https://example.com/second.jpg")
        TripImageFactory(trip=trip, order=1, image="https://example.com/first.jpg")

        self.assertEqual(trip.poster, "https://example.com/first.jpg")

    def test_poster_falls_back_to_metadata_without_trip_images(self):
        """Trip.poster should fall back to legacy metadata['poster'] when there's no TripImage."""
        trip = TripFactory(
            metadata={"poster": "https://example.com/legacy-poster.jpg"},
            trip_schedule=None,
        )
        self.assertEqual(trip.poster, "https://example.com/legacy-poster.jpg")

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

    def test_trip_availability(self):
        """Test the active() manager filters by the active date window."""
        trip = get_trip(trip_schedules=None)

        TripScheduleFactory(
            trip=trip,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=7),
        )
        self.assertEqual(TripSchedule.objects.active().filter(trip=trip).count(), 0)

        TripScheduleFactory(
            trip=trip,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=7),
        )
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

    def test_refund_policy(self):
        """
        Tests refund policy override.

        When trip's host has its own refund policy, it should be given
        preference over the generic host-wide RefundPolicy default.
        """
        self.trip.host.refund_policy = {}
        self.trip.host.save()

        common_policy = "Common trip RefundPolicy"
        RefundPolicy(description=common_policy).save()

        self.assertEqual(self.trip.refund_policy, RefundPolicy.current().description)

        new_refund_policy = "new refund policy"
        self.trip.host.refund_policy = new_refund_policy
        self.trip.host.save()
        self.assertEqual(self.trip.refund_policy, new_refund_policy)

    def test_repr(self):
        self.assertIn(self.trip.name, repr(self.trip))

    def test_get_absolute_url(self):
        self.assertIn(self.trip.slug, self.trip.get_absolute_url())


class TripImageStrReprTestCase(TestCase):
    def test_str_and_repr(self):
        image = TripImageFactory(order=1)
        self.assertIn(f"image #{image.order}", str(image))
        self.assertIn("TripImage", repr(image))


class TripCreateSchedulesTestCase(TestCase):
    """Trip.create_schedules() expands a DAILY TripAvailability into concrete
    TripSchedule rows - see the method's docstring in models.py for the full
    expansion flow this covers."""

    def make_trip(self):
        return TripFactory(trip_schedule=None)

    def test_no_availability_returns_zero(self):
        trip = self.make_trip()
        self.assertEqual(trip.create_schedules(), 0)

    def test_non_daily_availability_returns_zero(self):
        trip = self.make_trip()
        TripAvailability.objects.create(trip=trip, type=AvailabilityType.WEEKLY)
        self.assertEqual(trip.create_schedules(), 0)

    def test_missing_required_options_returns_zero(self):
        trip = self.make_trip()
        TripAvailability.objects.create(
            trip=trip, type=AvailabilityType.DAILY, options={"date_from": 1}
        )
        self.assertEqual(trip.create_schedules(), 0)

    def test_unparseable_option_timestamps_returns_zero(self):
        trip = self.make_trip()
        TripAvailability.objects.create(
            trip=trip,
            type=AvailabilityType.DAILY,
            options={
                "date_from": "not-a-timestamp",
                "end_date": "not-a-timestamp",
                "is_per_person_price": True,
            },
        )
        self.assertEqual(trip.create_schedules(), 0)

    def test_outside_scheduling_window_returns_zero(self):
        trip = self.make_trip()
        past_start = timezone.now() - timedelta(days=30)
        past_end = timezone.now() - timedelta(days=20)
        TripAvailability.objects.create(
            trip=trip,
            type=AvailabilityType.DAILY,
            options={
                "date_from": int(past_start.timestamp() * 1000),
                "end_date": int(past_end.timestamp() * 1000),
                "is_per_person_price": True,
            },
        )
        self.assertEqual(trip.create_schedules(), 0)

    def test_creates_schedule_for_each_day_within_window(self):
        trip = self.make_trip()
        start = timezone.now() - timedelta(days=1)
        end = timezone.now() + timedelta(days=4)
        availability = TripAvailability.objects.create(
            trip=trip,
            price=5000,
            available_seats=10,
            type=AvailabilityType.DAILY,
            options={
                "date_from": int(start.timestamp() * 1000),
                "end_date": int(end.timestamp() * 1000),
                "is_per_person_price": True,
            },
        )
        created_count = trip.create_schedules()
        self.assertEqual(created_count, trip.schedules.count())
        self.assertGreater(created_count, 0)
        for schedule in trip.schedules.all():
            self.assertEqual(schedule.price, availability.price)
            self.assertEqual(schedule.available_seats, availability.available_seats)
            self.assertEqual(schedule.booked_seats, 0)

    def test_capped_at_twenty_days(self):
        trip = self.make_trip()
        start = timezone.now() - timedelta(days=1)
        end = timezone.now() + timedelta(days=60)
        TripAvailability.objects.create(
            trip=trip,
            type=AvailabilityType.DAILY,
            options={
                "date_from": int(start.timestamp() * 1000),
                "end_date": int(end.timestamp() * 1000),
                "is_per_person_price": True,
            },
        )
        created_count = trip.create_schedules()
        self.assertEqual(created_count, 20)

    def test_second_call_is_idempotent(self):
        """Re-running create_schedules() shouldn't duplicate already-created days."""
        trip = self.make_trip()
        start = timezone.now() - timedelta(days=1)
        end = timezone.now() + timedelta(days=4)
        TripAvailability.objects.create(
            trip=trip,
            type=AvailabilityType.DAILY,
            options={
                "date_from": int(start.timestamp() * 1000),
                "end_date": int(end.timestamp() * 1000),
                "is_per_person_price": True,
            },
        )
        first_run = trip.create_schedules()
        second_run = trip.create_schedules()
        self.assertGreater(first_run, 0)
        self.assertEqual(second_run, 0)


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

    def test_str_and_repr(self):
        schedule = TripScheduleFactory()
        self.assertIn(str(schedule.start_date), str(schedule))
        self.assertIn("TripSchedule", repr(schedule))

    def test_is_active_true_within_window(self):
        schedule = TripScheduleFactory(
            start_date=(timezone.now() - timedelta(days=1)).date(),
            end_date=(timezone.now() + timedelta(days=1)).date(),
        )
        self.assertTrue(schedule.is_active)

    def test_is_active_false_outside_window(self):
        schedule = TripScheduleFactory(
            start_date=(timezone.now() + timedelta(days=1)).date(),
            end_date=(timezone.now() + timedelta(days=2)).date(),
        )
        self.assertFalse(schedule.is_active)

    def test_is_active_false_without_dates(self):
        schedule = TripScheduleFactory(start_date=None, end_date=None)
        self.assertFalse(schedule.is_active)


class TripAvailabilityTestCase(TestCase):
    def test_str(self):
        availability = TripAvailability.objects.create(
            trip=TripFactory(trip_schedule=None),
            price=1500,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=5)).date(),
        )
        self.assertIn(str(availability.price), str(availability))

    def test_is_active_true_within_window(self):
        availability = TripAvailability.objects.create(
            trip=TripFactory(trip_schedule=None),
            start_date=(timezone.now() - timedelta(days=1)).date(),
            end_date=(timezone.now() + timedelta(days=1)).date(),
        )
        self.assertTrue(availability.is_active)

    def test_is_active_false_outside_window(self):
        availability = TripAvailability.objects.create(
            trip=TripFactory(trip_schedule=None),
            start_date=(timezone.now() + timedelta(days=1)).date(),
            end_date=(timezone.now() + timedelta(days=2)).date(),
        )
        self.assertFalse(availability.is_active)

    def test_is_active_false_without_dates(self):
        availability = TripAvailability.objects.create(
            trip=TripFactory(trip_schedule=None)
        )
        self.assertFalse(availability.is_active)


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

    def test_str_and_repr(self):
        self.assertIn(str(self.itinerary.day_index), str(self.itinerary))
        self.assertIn("TripItinerary", repr(self.itinerary))

    def test_duration_property(self):
        expected = self.itinerary.end_time - self.itinerary.start_time
        self.assertEqual(self.itinerary.duration, expected)


class TripReviewLocationTestCase(TestCase):
    def test_location_defaults_to_none(self):
        """TripReview.location should be optional, defaulting to None."""
        review = TripReviewFactory(location=None)
        self.assertIsNone(review.location)

    def test_location_can_be_set(self):
        """TripReview.location should accept a Location instance."""
        location = LocationFactory(name="Lahore")
        review = TripReviewFactory(location=location)
        self.assertEqual(review.location, location)

    def test_location_set_null_on_delete(self):
        """Deleting a Location should null out any TripReview.location referencing it."""
        location = LocationFactory(name="Hunza")
        review = TripReviewFactory(location=location)
        location.delete()
        review.refresh_from_db()
        self.assertIsNone(review.location)

    def test_str_and_repr(self):
        review = TripReviewFactory(name="Ali", overall=5)
        self.assertIn("Ali", str(review))
        self.assertIn("TripReview", repr(review))


class TripReviewSummaryTestCase(TestCase):
    def test_str_and_repr(self):
        summary = TripReviewSummaryFactory()
        self.assertIn(str(summary.meals), str(summary))
        self.assertIn("TripReviewSummary", repr(summary))


class TripOptionTestCase(TestCase):
    def test_str_and_repr(self):
        option = TripOptionFactory()
        self.assertEqual(str(option), option.name)
        self.assertIn(option.name, repr(option))


class TestimonialTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.testimonial = TestimonialFactory()

    def test_create(self):
        self.assertIsInstance(self.testimonial, Testimonial)
        self.assertIsNotNone(self.testimonial.id)
        self.assertTrue(self.testimonial.is_verified)
        self.assertTrue(self.testimonial.is_active)

    def test_location_optional(self):
        testimonial = TestimonialFactory(location=None)
        self.assertIsNone(testimonial.location)

    def test_location_set_null_on_delete(self):
        location = LocationFactory(name="Skardu")
        testimonial = TestimonialFactory(location=location)
        location.delete()
        testimonial.refresh_from_db()
        self.assertIsNone(testimonial.location)

    def test_verified_manager_filters_unverified(self):
        TestimonialFactory(is_verified=True)
        TestimonialFactory(is_verified=False)
        verified = Testimonial.objects.verified()
        self.assertTrue(all(t.is_verified for t in verified))
        self.assertFalse(any(not t.is_verified for t in verified))

    def test_active_manager_filters_inactive(self):
        TestimonialFactory(is_active=True)
        TestimonialFactory(is_active=False)
        active = Testimonial.objects.active()
        self.assertTrue(all(t.is_active for t in active))

    def test_ordering_is_newest_first(self):
        older = TestimonialFactory()
        newer = TestimonialFactory()
        testimonials = list(Testimonial.objects.filter(id__in=[older.id, newer.id]))
        self.assertEqual(testimonials[0], newer)
        self.assertEqual(testimonials[1], older)

    def test_str_and_repr(self):
        testimonial = TestimonialFactory(name="Sara", quote="Loved the trip")
        self.assertIn("Sara", str(testimonial))
        self.assertIn("Sara", repr(testimonial))


class PolicyStrReprTestCase(TestCase):
    def test_cancellation_policy(self):
        policy = CancellationPolicy(description="No refunds after 7 days")
        policy.save()
        self.assertEqual(str(policy), "No refunds after 7 days")
        self.assertIn("No refunds after 7 days", repr(policy))

    def test_refund_policy(self):
        policy = RefundPolicy(description="Full refund within 7 days")
        policy.save()
        self.assertEqual(str(policy), "Full refund within 7 days")
        self.assertIn("Full refund within 7 days", repr(policy))


class TripBookingModelTestCase(TestCase):
    def test_str_and_repr(self):
        booking = TripBookingFactory(full_name="Jane Doe")
        self.assertIn("Jane Doe", str(booking))
        self.assertIn("Jane Doe", repr(booking))

    def test_manager_active_excludes_past_target_dates(self):
        past_booking = TripBookingFactory(
            target_date=timezone.now() - timedelta(days=1)
        )
        future_booking = TripBookingFactory(
            target_date=timezone.now() + timedelta(days=1)
        )
        active_ids = set(TripBooking.objects.active().values_list("id", flat=True))
        self.assertIn(future_booking.id, active_ids)
        self.assertNotIn(past_booking.id, active_ids)


class TripPickupLocationTestCase(TestCase):
    def test_str_and_repr(self):
        schedule = TripScheduleFactory()
        location = LocationFactory(name="Naran")
        pickup = TripPickupLocation.objects.create(
            trip=schedule, location=location, additional_price=100
        )
        self.assertEqual(str(pickup), str(location))
        self.assertIn("TripPickupLocation", repr(pickup))


class TripWishlistTestCase(TestCase):
    def test_create(self):
        wishlist_entry = TripWishlistFactory()
        self.assertIsInstance(wishlist_entry, TripWishlist)
        self.assertIsNotNone(wishlist_entry.id)
        self.assertIsNotNone(wishlist_entry.created_at)

    def test_str_and_repr(self):
        wishlist_entry = TripWishlistFactory()
        self.assertIn(str(wishlist_entry.trip), str(wishlist_entry))
        self.assertIn("TripWishlist", repr(wishlist_entry))

    def test_user_trip_pair_is_unique(self):
        """A user can't wishlist the same trip twice."""
        user = UserFactory()
        trip = TripFactory(trip_schedule=None)
        TripWishlistFactory(user=user, trip=trip)
        with self.assertRaises(IntegrityError):
            TripWishlistFactory(user=user, trip=trip)

    def test_same_trip_wishlisted_by_different_users(self):
        trip = TripFactory(trip_schedule=None)
        first = TripWishlistFactory(trip=trip)
        second = TripWishlistFactory(trip=trip)
        self.assertEqual(trip.wishlisted_by.count(), 2)
        self.assertIn(first, trip.wishlisted_by.all())
        self.assertIn(second, trip.wishlisted_by.all())

    def test_deleting_trip_removes_wishlist_entry(self):
        trip = TripFactory(trip_schedule=None)
        wishlist_entry = TripWishlistFactory(trip=trip)
        trip.delete()
        self.assertFalse(
            TripWishlist.objects.filter(id=wishlist_entry.id).exists()
        )

    def test_deleting_user_removes_wishlist_entry(self):
        user = UserFactory()
        wishlist_entry = TripWishlistFactory(user=user)
        user.delete()
        self.assertFalse(
            TripWishlist.objects.filter(id=wishlist_entry.id).exists()
        )
