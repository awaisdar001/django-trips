"""Signal receivers for django_trips."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from django_trips.choices import PackageTier
from django_trips.models import Trip, TripPackage


@receiver(post_save, sender=Trip)
def create_standard_package(sender, instance, created, **kwargs):  # pylint:disable=unused-argument
    """
    Every Trip must always have exactly one Standard TripPackage, starting at
    base_price=0 until an admin sets a real price. get_or_create keeps this
    idempotent regardless of how many times/ways a Trip ends up saved.
    """
    if not created:
        return
    TripPackage.objects.get_or_create(
        trip=instance,
        name=PackageTier.STANDARD,
        defaults={"base_price": 0, "base_child_price": 0},
    )
