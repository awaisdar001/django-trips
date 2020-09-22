# -*- coding: utf-8 -*-

import random
from datetime import datetime, timedelta

from django.utils.text import slugify
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from trips.models import (
    Facility, Host, Location, Trip, TripItinerary, Category, TripSchedule
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

    @staticmethod
    def get_random_host():
        """
        Get a random host from a pre-defined list of hosts
        """
        host_list = [
            'Arbisoft', 'Traverse', 'Travel Freaks', 'Destivels', 'Arbitainment'
        ]
        host, __ = Host.objects.get_or_create(name=random.choice(host_list), verified=True)
        return host

    @staticmethod
    def get_random_locations(locations_count=0):
        """
        Get multiple/single location object from pre-defined list.

        :param locations_count: If 0, only 1 object is returned,
        and if 1, random list of location objects is returned.
        """

        locations_names_list = [
            'Fairy Meadows', 'Hunza', 'Gilgit', 'Lahore', 'Islamabad',
            'Karachi', 'Kashmir', 'Murree', 'Kaghan', 'Swat', 'Skardu'
        ]

        def get_location_instance(name=None):
            name = name or random.choice(locations_names_list)
            location_data = {
                'name': name,
                'slug': slugify(name),
                'is_destination': random.choice([True, False]),
            }
            location_data['is_departure'] = not location_data['is_destination']
            return location_data

        if locations_count == 0:
            location_data = get_location_instance()
            location, __ = Location.objects.get_or_create(
                slug=location_data['slug'],
                defaults=location_data
            )
            return location

        trip_random_locations = []
        for location_name in random.sample(locations_names_list, random.choice(range(2, 7))):
            location_data = get_location_instance(location_name)
            location, __ = Location.objects.get_or_create(slug=location_data['slug'], defaults=location_data)
            trip_random_locations.append(location)
        return trip_random_locations

    @staticmethod
    def get_random_facilities():
        """
        Get random number of facilities from some pre-defined facilities.
        """
        facilities_names_list = [
            'Transport', 'Meals', 'Guide', 'Photography', 'Accommodation',
            'First Aid Kit', 'Bon Fire', 'Power Bank'
        ]
        facilities_objects_list = []
        for facility_name in random.sample(facilities_names_list, random.choice(range(2, 5))):
            facility, __ = Facility.objects.get_or_create(
                name=facility_name,
                defaults={'slug': slugify(facility_name)}
            )
            facilities_objects_list.append(facility)
        return facilities_objects_list

    @staticmethod
    def get_random_category():
        """
        Get random number of facilities from some pre-defined facilities.
        """
        category_names_list = [
            'Long Drive', 'Honeymoon', 'Rode Trip', 'Bone fire', 'Hiking',
        ]
        name = random.choice(category_names_list)
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
            schedule = datetime.now() + timedelta(days=trip_duration + (data_range * 7))
            schedules_list.append(schedule)
        return schedules_list

    @staticmethod
    def get_random_itineraries():
        """
        generate random itineraries for a trip with a defined format
        """
        return [
            (day, "Itinerary for Day: {}".format(day))
            for day in range(1, random.choice(range(4, 7)))
        ]

    @staticmethod
    def get_random_gear():
        """
        get random number of gears for a trip.

        returns a comma-separated string of gears from a pre-defined
        list of gears
        """
        gears_list = [
            'Mountain Climber', 'Shoes', 'Stick', 'Coat', 'Camp',
            'Inhaler', 'Lighter'
        ]
        selected_gear = random.sample(gears_list, random.choice(range(1, 4)))
        return ','.join(selected_gear)

    def handle(self, *args, **options):
        """
        Generating trip based on the input.
        """
        batch_size = options['batch_size']
        # user required to create a trip
        user = User.objects.get(username='admin')
        if not user:
            raise CommandError(
                "Username: admin doesn't exist. Run 'make import' to populate base data"
            )

        for count in range(0, batch_size):
            trip = Trip(name="Trip : {}".format(count))
            trip.destination = self.get_random_locations()
            trip.duration = random.choice(range(3, 8))
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
                    'Error Saving Trip {}\n{}'.format(trip.id, e)))

            # Adding M2M fields for the trip
            trip.locations.set(self.get_random_locations(4))
            trip.facilities.set(self.get_random_facilities())
            trip.save()

            # Setting Schedule & Itinerary
            trip_schedules = self.get_random_schedules(trip.duration)
            for schedule in trip_schedules:
                schedule = make_aware(schedule)
                price = random.choice([1000, 5000, 6000, 9000])
                trip_schedule = TripSchedule(trip=trip, date_from=schedule, price=price)
                trip_schedule.save()

            trip_itineraries = self.get_random_itineraries()
            for itinerary in trip_itineraries:
                trip_itinerary = TripItinerary(
                    trip=trip, day=itinerary[0], heading="Day {}".format(itinerary[0]), description=itinerary[1]
                )
                trip_itinerary.save()

            trip.name = "{} days trip to {}".format(len(trip_itineraries), trip.locations.first().name)
            trip.slug = slugify(trip.name)
            trip.save()
            self.stdout.write(self.style.SUCCESS('Trip Created: %s') % trip.name)
