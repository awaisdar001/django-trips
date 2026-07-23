"""Test management command"""
from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils.text import slugify

from django_trips.management.commands.generate_trips import Command
from django_trips.models import Location, Trip, User
from django_trips.tests import factories


class CommandsTestBase(TestCase):
    """
    Command for creating random trips.
    """

    def setUp(self):
        self.superuser = factories.UserFactory.create(is_superuser=True)
        super().setUp()

    def run_generate_trips_command(self, *args, **kwargs):
        """
        Calls the test command and outputs a dict of the current context.
        """
        out = StringIO()
        call_command('generate_trips', *args, stdout=out, **kwargs)
        out.seek(0)
        return out.read().strip()

    def test_command(self):
        trip_count = 10
        kwargs = {'batch_size': trip_count}
        output = self.run_generate_trips_command(*(), **kwargs)
        self.assertEqual(output.count('Trip Created'), trip_count)

    def test_generated_trips_have_working_region(self):
        """Generated trips' destination/departure should resolve a region,
        not None - this is what the Trips page needs to show a place."""
        self.run_generate_trips_command(batch_size=5)
        for trip in Trip.objects.all():
            self.assertIsNotNone(
                trip.destination.region, f"{trip.destination} has no region"
            )
            self.assertIsNotNone(
                trip.departure.region, f"{trip.departure} has no region"
            )

    def test_generated_trips_have_poster_and_reviews(self):
        """Generated trips should have a poster image and review data,
        not the empty/zero defaults - otherwise trip cards render blank."""
        self.run_generate_trips_command(batch_size=3)
        for trip in Trip.objects.all():
            self.assertTrue(trip.poster, f"{trip} has no poster")
            self.assertTrue(trip.reviews.exists(), f"{trip} has no reviews")

    def test_backfills_region_for_preexisting_location(self):
        """
        A Location that already exists (e.g. seeded before this region
        mapping existed, or before this command's first run) but has no
        parent should get backfilled the next time it's touched, not left
        with a permanently None region.

        Calls Command.get_or_create_location directly (rather than running
        the full batch and relying on it randomly picking "Karachi") so
        this test is deterministic.
        """
        preexisting = Location.objects.create(
            name="Karachi", slug=slugify("Karachi")
        )
        self.assertIsNone(preexisting.region)

        Command().get_or_create_location("Karachi")

        preexisting.refresh_from_db()
        self.assertIsNotNone(preexisting.parent)
        self.assertEqual(preexisting.region, "Sindh")

    def test_raises_without_a_superuser(self):
        """The command requires a superuser to attribute generated trips to."""
        User.objects.filter(is_superuser=True).delete()
        with self.assertRaises(CommandError) as ctx:
            call_command("generate_trips", batch_size=1)
        self.assertIn("No superuser found", str(ctx.exception))

    def test_wraps_unexpected_errors_in_command_error(self):
        """An error mid-generation should surface as a CommandError, not crash."""
        with patch.object(
            Command, "create_trip", side_effect=ValueError("boom")
        ):
            with self.assertRaises(CommandError) as ctx:
                self.run_generate_trips_command(batch_size=1)
        self.assertIn("Error creating trip", str(ctx.exception))

    def test_get_region_for_location_returns_none_when_unmapped(self):
        """A location name not present in TRIP_LOCATIONS_BY_REGION has no region."""
        self.assertIsNone(Command().get_region_for_location("Nowhereville"))

    def test_create_reviews_returns_none_without_verified_reviews(self):
        """create_reviews() should skip building a TripReviewSummary when
        every generated review happens to be unverified."""
        trip = factories.TripFactory(trip_schedule=None)
        with patch("django_trips.management.commands.generate_trips.random") as mock_random:
            mock_random.randint.return_value = 3
            mock_random.random.return_value = 1.0  # is_verified = random() < 0.8 -> False
            result = Command().create_reviews(trip)
        self.assertIsNone(result)
        self.assertFalse(trip.reviews.filter(is_verified=True).exists())
