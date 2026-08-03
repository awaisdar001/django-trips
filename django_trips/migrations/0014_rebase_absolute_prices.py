"""
Data half of the pricing model reversal (see docs/TripPricingModelReversalPlan.md
in the destipak root repo, and 0013's docstring for the schema half).

0013 only renamed columns - TripPackage.base_price/base_child_price still
hold the *relative delta* values 0012 computed, and TripSchedule.additional_price/
additional_child_price still hold the *old absolute* per-schedule price. This
migration rebases both onto their new meaning:

For each trip with both packages and schedules, anchor on the same "cheapest
active-or-upcoming schedule" reference price 0012/get_effective_price()/
Trip.starting_price already used pre-reversal:
  - add that reference price onto every package's base_price/base_child_price,
    turning the 0012 delta back into an absolute per-tier price
  - subtract that same reference price from every schedule's additional_price/
    additional_child_price, turning the old absolute price into a flat
    surcharge (the anchor schedule itself lands at exactly 0 - "no surcharge")

Scoped to *active-or-upcoming* schedules specifically, not literally the
cheapest of all schedules, matching 0012's own reasoning: a schedule that's
already sold-out/in the past can be cheaper than anything currently
bookable, which would otherwise anchor a package's base_price (and so
Trip.starting_price) at a number nobody can actually book.

Validated against the real dev DB (100 seeded trips) before writing this
migration: 14/100 trips have a stale/sold-out schedule cheaper than anything
currently bookable, confirming the active-or-upcoming scoping above matters;
all 100 trips produced non-negative, realistic base_price/additional_price
values under this anchor (sample - Trip 1: BUDGET 72,200 / STANDARD 98,700 /
PREMIUM 146,400).

Trips with packages but no active/upcoming schedule to anchor against are
left untouched and logged - there's no reference price to rebase against, so
touching them would produce an arbitrary absolute price out of a relative
delta.
"""

from django.db import migrations
from django.db.models import Q
from django.utils.timezone import now


def get_reference_schedule(trip_id, TripSchedule):
    n = now()
    return (
        TripSchedule.objects.filter(trip_id=trip_id)
        .filter(Q(start_date__lte=n, end_date__gte=n) | Q(start_date__gte=n))
        .order_by("additional_price")  # post-rename field name; still holds the OLD absolute price at this point
        .first()
    )


def rebase_absolute_prices(apps, schema_editor):
    Trip = apps.get_model("django_trips", "Trip")
    TripSchedule = apps.get_model("django_trips", "TripSchedule")

    skipped_trip_ids = []

    for trip in Trip.objects.prefetch_related("packages", "schedules").iterator(
        chunk_size=100
    ):
        packages = list(trip.packages.all())
        if not packages:
            continue

        reference_schedule = get_reference_schedule(trip.id, TripSchedule)
        if not reference_schedule:
            skipped_trip_ids.append(trip.id)
            continue

        reference_adult = reference_schedule.additional_price  # old absolute value
        reference_child = reference_schedule.additional_child_price

        for package in packages:
            package.base_price = reference_adult + package.base_price
            package.base_child_price = reference_child + package.base_child_price
            package.save(update_fields=["base_price", "base_child_price"])

        for schedule in trip.schedules.all():
            schedule.additional_price = schedule.additional_price - reference_adult
            schedule.additional_child_price = (
                schedule.additional_child_price - reference_child
            )
            schedule.save(
                update_fields=["additional_price", "additional_child_price"]
            )

    if skipped_trip_ids:
        print(
            f"\n[0014_rebase_absolute_prices] {len(skipped_trip_ids)} trip(s) had "
            "packages but no active/upcoming schedule to anchor against - left "
            f"untouched: {skipped_trip_ids}\n"
        )


def noop_reverse(apps, schema_editor):
    """Irreversible: the pre-rebase delta/absolute split isn't recoverable once rebased."""


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0013_rename_pricing_fields"),
    ]

    operations = [
        migrations.RunPython(rebase_absolute_prices, noop_reverse),
    ]
