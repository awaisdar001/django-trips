"""Pricing calculations spanning TripSchedule/TripPackage/TripPickupLocation."""


def get_effective_price(schedule, package=None, pickup=None):
    """
    Resolve the final per-person price for a specific schedule.

    `schedule.price`/`schedule.child_price` are the source-of-truth base
    price for that departure date. `package.additional_price`/
    `additional_child_price` are deltas added on top of it (always 0 for the
    Standard tier - see `TripPackage.clean()`). `pickup.additional_price` is
    a flat surcharge added to both the adult and child price alike.
    """
    delta_adult = package.additional_price if package else 0
    delta_child = package.additional_child_price if package else 0
    pickup_addl = pickup.additional_price if pickup else 0

    return {
        "price": schedule.price + delta_adult + pickup_addl,
        "child_price": schedule.child_price + delta_child + pickup_addl,
    }
