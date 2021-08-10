from datetime import datetime

from django.db import models
from pytz import UTC


class AvailableTripScheduleManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> TripSchedule.available.all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which have date_from defined
        in the future
        """
        return super(AvailableTripScheduleManager, self).get_queryset().filter(
            date_from__gt=datetime.now(tz=UTC)
        )


class AvailableLocationManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> Location.available.all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which are active.
        """
        return super().get_queryset().filter(is_active=True)


class ActiveModelManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> Trip.active.all()
        >>> Trip.trip_schedule(manager='active').all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which have date_from defined
        in the future
        """
        return super(ActiveModelManager, self).get_queryset().filter(
            deleted=False
        )


class TripDestinationManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> Location.destinations.all()
        >>> Trip.locations(manager='destinations').all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which have date_from defined
        in the future
        """
        return super(TripDestinationManager, self).get_queryset().filter(
            is_destination=True
        )


class TripDepartureManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> Location.departures.all()
        >>> Trip.locations(manager='departures').all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which have date_from defined
        in the future
        """
        return super(TripDepartureManager, self).get_queryset().filter(
            is_departure=True
        )
