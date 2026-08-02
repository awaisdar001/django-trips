from django.test import TestCase

from django_trips.choices import PackageTier
from django_trips.services import get_effective_price
from django_trips.tests.factories import (
    TripPackageFactory,
    TripPickupLocationFactory,
    TripScheduleFactory,
)


class GetEffectivePriceTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.schedule = TripScheduleFactory(price=10000, child_price=6000)

    def test_no_package_or_pickup_returns_schedule_price(self):
        result = get_effective_price(self.schedule)
        self.assertEqual(result, {"price": 10000, "child_price": 6000})

    def test_package_only_adds_its_deltas(self):
        package = TripPackageFactory(
            name=PackageTier.PREMIUM, additional_price=2000, additional_child_price=1000
        )
        result = get_effective_price(self.schedule, package=package)
        self.assertEqual(result, {"price": 12000, "child_price": 7000})

    def test_pickup_only_adds_flat_surcharge_to_both(self):
        pickup = TripPickupLocationFactory(schedule=self.schedule, additional_price=500)
        result = get_effective_price(self.schedule, pickup=pickup)
        self.assertEqual(result, {"price": 10500, "child_price": 6500})

    def test_package_and_pickup_combine(self):
        package = TripPackageFactory(
            name=PackageTier.BUDGET, additional_price=-1000, additional_child_price=-500
        )
        pickup = TripPickupLocationFactory(schedule=self.schedule, additional_price=500)
        result = get_effective_price(self.schedule, package=package, pickup=pickup)
        self.assertEqual(result, {"price": 9500, "child_price": 6000})

    def test_standard_package_is_a_zero_delta_noop(self):
        """The Standard tier's deltas are always 0 (enforced by
        TripPackage.clean()), so it should resolve to the raw schedule
        price - the whole point of it being the default tier."""
        standard = self.schedule.trip.packages.get(name=PackageTier.STANDARD)
        result = get_effective_price(self.schedule, package=standard)
        self.assertEqual(result, {"price": 10000, "child_price": 6000})
