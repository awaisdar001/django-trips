"""Test management command"""
from django.core.management import call_command
from django.test import TestCase
from django_trips.tests import factories
from six import StringIO


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
