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


class ActiveTripManager(models.Manager):
    """
    Trip schedule safe queryset manager.

    Usage:
        >>> Trip.active.all()
        >>> Trip.trip_schedule(manager='available').all()
    """

    def get_queryset(self):
        """
        This method will only return the objects which have date_from defined
        in the future
        """
        return super(ActiveTripManager, self).get_queryset().filter(
            deleted=False
        )
