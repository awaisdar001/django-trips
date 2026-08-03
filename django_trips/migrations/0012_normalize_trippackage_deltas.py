"""
Rebase legacy TripPackage price deltas onto the additive-delta pricing model.

Before the pricing refactor (migrations 0007-0010), TripPackage.additional_price
(then base_price) held an absolute per-adult price for that tier - a second,
competing price alongside TripSchedule.price rather than a delta added on top
of it. 0007 renamed the field but kept the stored values verbatim, and 0008's
own docstring flagged the fallout without fixing it: every existing STANDARD
package still carried that non-zero absolute price, which get_effective_price()
now adds directly on top of a schedule's price - roughly doubling the total
shown to a traveler (see the trip in the review screenshot: schedule 47,900 +
leftover "delta" 45,800 = 93,700).

For each trip, this rebases every package's delta against a reference price:
  - the trip's own (pre-rebase) STANDARD package price, when it was non-zero -
    this was the tier system's original per-trip baseline, so subtracting it
    out preserves however BUDGET/PREMIUM were originally spaced relative to
    it, just re-based to be relative instead of absolute
  - falling back to the trip's cheapest active/upcoming schedule price (the
    same reference TripPackageSerializer.effective_price and
    Trip.starting_price already use) for the ~34 trips backfilled with a
    zero-delta STANDARD by 0008, which never had an absolute baseline to
    begin with

STANDARD itself always ends up at exactly (0, 0), satisfying the invariant
TripPackage.clean() enforces on every future save. Trips with packages but no
resolvable reference price (none found in this dataset, but possible in
principle) are left untouched and logged.
"""

from django.db import migrations
from django.db.models import Q
from django.utils.timezone import now

STANDARD = "STANDARD"


def get_reference_schedule(trip_id, TripSchedule):
    n = now()
    return (
        TripSchedule.objects.filter(trip_id=trip_id)
        .filter(Q(start_date__lte=n, end_date__gte=n) | Q(start_date__gte=n))
        .order_by("price")
        .first()
    )


def rebase_package_deltas(apps, schema_editor):
    Trip = apps.get_model("django_trips", "Trip")
    TripPackage = apps.get_model("django_trips", "TripPackage")
    TripSchedule = apps.get_model("django_trips", "TripSchedule")

    skipped_trip_ids = []

    for trip in Trip.objects.prefetch_related("packages").iterator(chunk_size=100):
        packages = list(trip.packages.all())
        if not packages:
            continue

        standard = next((p for p in packages if p.name == STANDARD), None)
        adult_ref = standard.additional_price if standard and standard.additional_price else None
        child_ref = (
            standard.additional_child_price if standard and standard.additional_child_price else None
        )

        if adult_ref is None or child_ref is None:
            reference_schedule = get_reference_schedule(trip.id, TripSchedule)
            if adult_ref is None:
                adult_ref = reference_schedule.price if reference_schedule else None
            if child_ref is None:
                child_ref = reference_schedule.child_price if reference_schedule else None

        if adult_ref is None and child_ref is None:
            skipped_trip_ids.append(trip.id)
            continue

        for package in packages:
            if package.name == STANDARD:
                new_price, new_child_price = 0, 0
            else:
                new_price = package.additional_price - adult_ref if adult_ref is not None else package.additional_price
                new_child_price = (
                    package.additional_child_price - child_ref
                    if child_ref is not None
                    else package.additional_child_price
                )
            if package.additional_price != new_price or package.additional_child_price != new_child_price:
                package.additional_price = new_price
                package.additional_child_price = new_child_price
                package.save(update_fields=["additional_price", "additional_child_price"])

    if skipped_trip_ids:
        print(
            f"\n[0012_normalize_trippackage_deltas] {len(skipped_trip_ids)} trip(s) had "
            "packages but no resolvable reference price (no non-zero STANDARD "
            f"package and no active/upcoming schedule) - left untouched: {skipped_trip_ids}\n"
        )


def noop_reverse(apps, schema_editor):
    """Irreversible: the original absolute prices aren't recoverable once rebased."""


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0011_merge_20260802_0018"),
    ]

    operations = [
        migrations.RunPython(rebase_package_deltas, noop_reverse),
    ]
