"""Test management command"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils.text import slugify

from django_trips.management.commands.generate_trips import Command
from django_trips.models import Location, Trip
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
