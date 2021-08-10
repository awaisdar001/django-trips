# -*- coding: utf-8 -*-

import random
from collections import namedtuple
from datetime import datetime, timedelta

from dateutil.tz import UTC
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django_trips.models import (Category, Facility, Host, Location, Trip,
                                 TripItinerary, TripSchedule)

TRIP_DESTINATIONS = 'TRIP_DESTINATIONS'
TRIP_DEPARTURE_LOCATION = 'TRIP_DEPARTURE_LOCATION'
TRIP_LOCATIONS = 'TRIP_LOCATIONS'
TRIP_HOSTS = 'TRIP_HOSTS'
TRIP_FACILITIES = 'TRIP_FACILITIES'
TRIP_CATEGORIES = 'TRIP_CATEGORIES'
TRIP_GEARS = 'TRIP_GEARS'

DEFAULT_SETTINGS = namedtuple(
    'Settings',
    [TRIP_DESTINATIONS, TRIP_DEPARTURE_LOCATION, TRIP_LOCATIONS, TRIP_HOSTS, TRIP_FACILITIES,
     TRIP_CATEGORIES, TRIP_GEARS]
)

LocalSettings = DEFAULT_SETTINGS(
    ['Swat', 'Gilgit'], ['Lahore'], ['Lahore', 'Swat', 'Gilgit'], ['Django'], ['Bonefire', 'Food', 'Drinks'],
    ['Honymoon', 'Outdoor'], ['Sun glasses', 'Sun block']
)


class Command(BaseCommand):
    """
    This command will generate batch of trips with random data.

    By running this command, the trips generated will have random data
    from a pre-defined list of data. The data selection is done at the
    random to ensure that trips will have diverse data, which will provide
    help for filtering & searching.

    EXAMPLE USAGE:
        ./manage.py generate_trips --batch_size=100
    OR
        ./manage.py generate_trips

    If batch size is not provided, the command will generate 10 trips
    """

    help = "Generate batches of trip with pre-populated random data"

    def add_arguments(self, parser):
        """
        Defining the arguments to be used by the command.
        """
        parser.add_argument(
            '--batch_size',
            type=int,
            default=10,
            dest='batch_size',
            help="number to trips to generate"
        )

    def get_settings(self, setting_needed, default=None):
        value = getattr(settings, setting_needed, getattr(LocalSettings, setting_needed, default))
        assert value, f'Missing required settings {setting_needed}.'
        return value

    def get_random_host(self):
        """
        Get a random host from a pre-defined list of hosts
        """
        hosts = self.get_settings('TRIP_HOSTS')
        host, __ = Host.objects.get_or_create(name=random.choice(hosts), verified=True)
        return host

    def get_location_instance(self, name=None):
        name = name or random.choice(self.get_settings('TRIP_LOCATIONS'))
        location_data = {'name': name, 'slug': slugify(name)}
        return location_data

    def get_destination(self):
        name = random.choice(self.get_settings('TRIP_DESTINATIONS'))
        destination_data = {'name': name, 'slug': slugify(name), 'is_destination': True}
        destination, __ = Location.objects.get_or_create(
            slug=destination_data['slug'],
            defaults=destination_data
        )
        return destination

    def get_departure(self):
        name = random.choice(self.get_settings('TRIP_DESTINATIONS'))
        departure_location_data = {'name': name, 'slug': slugify(name), 'is_departure': True}
        departure, __ = Location.objects.get_or_create(
            slug=departure_location_data['slug'],
            defaults=departure_location_data
        )
        return departure

    def get_random_locations(self):
        """
        Get multiple/single location object from pre-defined list.
        """
        trip_random_locations = []
        locations = self.get_settings('TRIP_LOCATIONS')
        for location_name in random.sample(locations, random.choice(range(1, len(locations)))):
            location_data = self.get_location_instance(location_name)
            location, __ = Location.objects.get_or_create(slug=location_data['slug'], defaults=location_data)
            trip_random_locations.append(location)
        return trip_random_locations

    def get_random_facilities(self):
        """
        Get random number of facilities from some pre-defined facilities.
        """
        facilities_objects_list = []
        facilities = self.get_settings('TRIP_FACILITIES')
        for facility_name in random.sample(facilities, random.choice(range(1, len(facilities)))):
            facility, __ = Facility.objects.get_or_create(
                name=facility_name,
                defaults={'slug': slugify(facility_name)}
            )
            facilities_objects_list.append(facility)
        return facilities_objects_list

    def get_random_category(self):
        """
        Get random number of facilities from some pre-defined facilities.
        """
        name = random.choice(self.get_settings('TRIP_CATEGORIES'))
        category, __ = Category.objects.get_or_create(
            name=name,
            defaults={'slug': slugify(name)}
        )
        return category

    @staticmethod
    def get_random_schedules(trip_duration):
        """
        get random schedules datetime objects separated by appropriate trip duration.
        """
        schedules_list = []
        for data_range in range(1, random.choice(range(3, 6))):
            schedule = datetime.now(tz=UTC) + timedelta(days=trip_duration + (data_range * 7))
            schedules_list.append(schedule)
        return schedules_list

    @staticmethod
    def get_random_itineraries():
        """
        generate random itineraries for a trip with a defined format
        """
        return [
            (day, "Itinerary for Day: {}".format(day))
            for day in range(1, random.choice(range(5, 20)))
        ]

    def get_random_gear(self):
        """
        get random number of gears for a trip.

        returns a comma-separated string of gears from a pre-defined
        list of gears
        """
        trip_gear = self.get_settings('TRIP_GEARS')
        selected_gear = random.sample(trip_gear, random.choice(range(1, len(trip_gear))))
        return ','.join(selected_gear)

    def handle(self, *args, **options):
        """
        Generating trip based on the input.
        """
        batch_size = options['batch_size']
        # user required to create a trip
        super_users = User.objects.filter(is_superuser=True)
        if not super_users.count() > 0:
            raise CommandError("Superuser doesn't exist. Please create a superuser for the app.")
        user = super_users.first()

        for count in range(0, batch_size):
            trip = Trip(
                destination=self.get_destination(),
                departure=self.get_departure(),
            )
            trip_itineraries = self.get_random_itineraries()
            trip.duration = len(trip_itineraries)

            trip.name = "{} days trip to {}".format(trip.duration, trip.destination.name)

            trip.age_limit = random.choice(range(20, 40))
            trip.host = self.get_random_host()
            trip.gear = self.get_random_gear()
            trip.category = self.get_random_category()
            trip.description = "This is the description for trip: {}".format(count)
            trip.created_by = user

            # Initial Save
            try:
                trip.save()
            except Exception as e:
                raise CommandError(self.stderr.write(
                    'Error Saving Trip {}\n{}'.format(trip.name, e)))

            # Adding M2M fields for the trip
            trip.locations.set(self.get_random_locations())
            trip.facilities.set(self.get_random_facilities())
            trip.save()

            # Setting Schedule & Itinerary
            trip_schedules = self.get_random_schedules(trip.duration)
            price = random.choice([1000, 5000, 6000, 9000])
            for schedule in trip_schedules:
                price = random.choice([price - 500, price + 500])
                trip_schedule = TripSchedule(trip=trip, date_from=schedule, price=price)
                trip_schedule.save()

            for itinerary in trip_itineraries:
                trip_itinerary = TripItinerary(
                    trip=trip,
                    heading="Day {}".format(itinerary[0]),
                    description=itinerary[1],
                    day=itinerary[0],
                )
                trip_itinerary.save()

            self.stdout.write(self.style.SUCCESS('Trip Created: %s') % trip.name)
