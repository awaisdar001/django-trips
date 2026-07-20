"""Tests for the trip-card fields added to TripListSerializer/TripDetailSerializer:
poster, images, facilities, passenger limits, starting_price, duration
formatting, and review_summary.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from django_trips.choices import LocationType
from django_trips.tests.factories import (
    AuthenticatedUserTestCase,
    FacilityFactory,
    LocationFactory,
    TripFactory,
    TripImageFactory,
    TripReviewFactory,
    TripReviewSummaryFactory,
    TripScheduleFactory,
)
from django_trips.utils import format_trip_duration


@pytest.mark.django_db
class TestTripCardFields(AuthenticatedUserTestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("trips-api:trip-list")

    def get_detail(self, trip):
        url = reverse("trips-api:trip-detail", kwargs={"identifier": trip.slug})
        return self.client.get(url, headers=self.headers).json()

    def get_list_item(self, trip):
        response = self.client.get(self.list_url, {}, headers=self.headers)
        results = {item["slug"]: item for item in response.json()["results"]}
        return results[trip.slug]

    # -- poster --------------------------------------------------------

    def test_poster_from_metadata(self):
        """poster should reflect metadata['poster'] on both list and detail."""
        trip = TripFactory(
            metadata={"poster": "https://example.com/hunza.jpg"}, trip_schedule=None
        )
        self.assertEqual(self.get_detail(trip)["poster"], "https://example.com/hunza.jpg")
        self.assertEqual(
            self.get_list_item(trip)["poster"], "https://example.com/hunza.jpg"
        )

    def test_poster_defaults_to_empty_string(self):
        """poster should be '' (not crash) when metadata has no poster key."""
        trip = TripFactory(metadata={}, trip_schedule=None)
        self.assertEqual(self.get_detail(trip)["poster"], "")

    def test_poster_prefers_first_trip_image(self):
        """poster should use the first TripImage (by order) over metadata['poster']."""
        trip = TripFactory(
            metadata={"poster": "https://example.com/legacy.jpg"}, trip_schedule=None
        )
        TripImageFactory(trip=trip, order=2, image="https://example.com/second.jpg")
        TripImageFactory(trip=trip, order=1, image="https://example.com/first.jpg")
        self.assertEqual(self.get_detail(trip)["poster"], "https://example.com/first.jpg")

    # -- images (gallery) --------------------------------------------------

    def test_images_empty_when_no_gallery(self):
        """images should be an empty list when the trip has no TripImage rows."""
        trip = TripFactory(trip_schedule=None)
        self.assertEqual(self.get_detail(trip)["images"], [])
        self.assertEqual(self.get_list_item(trip)["images"], [])

    def test_images_ordered_and_serialized_on_detail(self):
        trip = TripFactory(trip_schedule=None)
        TripImageFactory(
            trip=trip, order=2, image="https://example.com/b.jpg", alt_text="B"
        )
        TripImageFactory(
            trip=trip, order=1, image="https://example.com/a.jpg", alt_text="A"
        )
        images = self.get_detail(trip)["images"]
        self.assertEqual([img["image"] for img in images], [
            "https://example.com/a.jpg",
            "https://example.com/b.jpg",
        ])
        self.assertEqual(images[0]["alt_text"], "A")
        self.assertEqual(images[0]["order"], 1)

    def test_images_present_on_list_endpoint_too(self):
        trip = TripFactory(trip_schedule=None)
        TripImageFactory(trip=trip, order=1, image="https://example.com/a.jpg")
        images = self.get_list_item(trip)["images"]
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["image"], "https://example.com/a.jpg")

    def test_images_scoped_to_own_trip(self):
        """A trip's images should not leak another trip's gallery."""
        trip = TripFactory(trip_schedule=None)
        other_trip = TripFactory(trip_schedule=None)
        TripImageFactory(trip=other_trip)
        self.assertEqual(self.get_detail(trip)["images"], [])

    # -- facilities ------------------------------------------------------

    def test_facilities_present_on_list_endpoint(self):
        """facilities should be serialized on the list endpoint, not just detail."""
        trip = TripFactory(
            facilities=["Breakfast included", "Local tour guide"], trip_schedule=None
        )
        list_names = {f["name"] for f in self.get_list_item(trip)["facilities"]}
        detail_names = {f["name"] for f in self.get_detail(trip)["facilities"]}
        self.assertEqual(list_names, {"Breakfast included", "Local tour guide"})
        self.assertEqual(list_names, detail_names)

    def test_facilities_empty_when_none_assigned(self):
        trip = TripFactory(trip_schedule=None)
        trip.facilities.clear()
        self.assertEqual(self.get_list_item(trip)["facilities"], [])

    def test_facility_icon_exposed(self):
        """Each facility's icon identifier should be serialized so the frontend
        doesn't need its own name -> icon lookup table."""
        trip = TripFactory(trip_schedule=None)
        trip.facilities.clear()
        facility = FacilityFactory(name="Breakfast included", icon="coffee")
        trip.facilities.add(facility)
        result = self.get_list_item(trip)["facilities"][0]
        self.assertEqual(result["name"], "Breakfast included")
        self.assertEqual(result["icon"], "coffee")

    def test_facilities_scoped_to_own_trip(self):
        """A trip's facilities list shouldn't include another trip's facilities."""
        trip = TripFactory(trip_schedule=None)
        trip.facilities.clear()
        other_trip = TripFactory(
            facilities=["Breakfast included"], trip_schedule=None
        )
        self.assertEqual(
            {f["name"] for f in self.get_list_item(other_trip)["facilities"]},
            {"Breakfast included"},
        )
        self.assertEqual(self.get_list_item(trip)["facilities"], [])

    # -- passenger limits --------------------------------------------------

    def test_passenger_limits_present_on_list_endpoint(self):
        """passenger_limit_min/max should be serialized on the list endpoint too."""
        trip = TripFactory(
            passenger_limit_min=2, passenger_limit_max=50, trip_schedule=None
        )
        list_item = self.get_list_item(trip)
        self.assertEqual(list_item["passenger_limit_min"], 2)
        self.assertEqual(list_item["passenger_limit_max"], 50)

    # -- starting_price --------------------------------------------------

    def test_starting_price_picks_cheapest_bookable_schedule(self):
        """starting_price should be the min price among active/upcoming schedules,
        ignoring past ones and picking the lowest even if it's not the first created."""
        trip = TripFactory(trip_schedule=None)
        now = timezone.now()
        # Past schedule - must be ignored even though it's the cheapest.
        TripScheduleFactory(
            trip=trip,
            price=100,
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=5),
        )
        # Upcoming schedules.
        TripScheduleFactory(
            trip=trip,
            price=20000,
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=8),
        )
        TripScheduleFactory(
            trip=trip,
            price=15000,
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=13),
        )
        self.assertEqual(int(self.get_detail(trip)["starting_price"]), 15000)

    def test_starting_price_none_without_bookable_schedule(self):
        """starting_price should be None when there's no active/upcoming schedule."""
        trip = TripFactory(trip_schedule=None)
        now = timezone.now()
        TripScheduleFactory(
            trip=trip,
            price=100,
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=5),
        )
        self.assertIsNone(self.get_detail(trip)["starting_price"])

    # -- duration ----------------------------------------------------------

    def test_duration_formatting_multi_day(self):
        trip = TripFactory(duration=timedelta(days=7), trip_schedule=None)
        self.assertEqual(self.get_detail(trip)["duration"], "7 Days 6 Nights")

    def test_duration_formatting_single_day(self):
        trip = TripFactory(duration=timedelta(days=1), trip_schedule=None)
        self.assertEqual(self.get_detail(trip)["duration"], "1 Day")

    def test_duration_formatting_helper_directly(self):
        self.assertEqual(format_trip_duration(timedelta(days=2)), "2 Days 1 Night")
        self.assertIsNone(format_trip_duration(None))
        self.assertIsNone(format_trip_duration(timedelta(days=0)))

    # -- review_summary ------------------------------------------------

    def test_review_summary_defaults_when_absent(self):
        """No TripReviewSummary and no reviews -> all-zero defaults, count 0."""
        trip = TripFactory(trip_schedule=None)
        summary = self.get_detail(trip)["review_summary"]
        self.assertEqual(
            summary,
            {
                "meals": 0,
                "accommodation": 0,
                "transport": 0,
                "value_for_money": 0,
                "overall": 0,
                "reviews_count": 0,
            },
        )

    def test_review_summary_reflects_curated_summary(self):
        trip = TripFactory(trip_schedule=None)
        TripReviewSummaryFactory(
            trip=trip,
            meals=4.5,
            accommodation=4.0,
            transport=3.5,
            value_for_money=4.2,
            overall=4.3,
        )
        summary = self.get_detail(trip)["review_summary"]
        self.assertEqual(float(summary["overall"]), 4.3)
        self.assertEqual(float(summary["meals"]), 4.5)

    def test_review_summary_counts_only_verified_reviews(self):
        trip = TripFactory(trip_schedule=None)
        TripReviewFactory.create_batch(2, trip=trip, is_verified=True)
        TripReviewFactory.create_batch(3, trip=trip, is_verified=False)
        summary = self.get_detail(trip)["review_summary"]
        self.assertEqual(summary["reviews_count"], 2)

    def test_review_summary_present_on_list_endpoint_too(self):
        trip = TripFactory(trip_schedule=None)
        TripReviewFactory(trip=trip, is_verified=True)
        summary = self.get_list_item(trip)["review_summary"]
        self.assertEqual(summary["reviews_count"], 1)

    # -- destination.region (Location hierarchy) ----------------------

    def test_destination_region_from_parent(self):
        province = LocationFactory(name="Gilgit-Baltistan", type=LocationType.PROVINCE)
        destination = LocationFactory(
            name="Hunza", type=LocationType.TOWN, parent=province
        )
        trip = TripFactory(destination=destination, trip_schedule=None)
        self.assertEqual(
            self.get_detail(trip)["destination"]["region"], "Gilgit-Baltistan"
        )
        self.assertEqual(
            self.get_list_item(trip)["destination"]["region"], "Gilgit-Baltistan"
        )

    def test_destination_region_none_when_unlinked(self):
        destination = LocationFactory(type=LocationType.TOWN, parent=None)
        trip = TripFactory(destination=destination, trip_schedule=None)
        self.assertIsNone(self.get_detail(trip)["destination"]["region"])
