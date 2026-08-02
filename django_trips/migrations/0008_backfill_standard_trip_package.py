"""
Backfill a zero-delta Standard TripPackage onto every Trip that doesn't
already have one (going forward, django_trips.signals.create_standard_package
keeps this true for every new Trip).

Pre-flight read-only report run against the destipak dev DB before writing
this migration (100 trips total):
    - trips_missing_standard: 34  (these get a new additional_price=0 row)
    - standard_packages_count: 66
    - nonzero_standard_packages: 66  (!) - every existing STANDARD package in
      that DB already carries a real, non-zero base_price/base_child_price
      (from the seed_trip_demo_data management command's seed_trip_packages(),
      which priced STANDARD the same as BUDGET/PREMIUM before this rename).

Per the task requirement, this migration does NOT zero out or otherwise
touch those pre-existing non-zero rows - that would be a real data change,
not a backfill of missing rows. It only creates the missing ones, and prints
a warning listing any non-zero STANDARD rows it finds so they can be
reviewed/reconciled manually (e.g. via a follow-up decision on whether that
price data should move onto the schedule, become a differently-named tier,
or be zeroed deliberately).
"""

from django.db import migrations

STANDARD = "STANDARD"


def report_nonzero_standard_packages(TripPackage):
    """Read-only: log any STANDARD package that already carries a non-zero
    price delta, so this backfill doesn't silently paper over real data."""
    nonzero = TripPackage.objects.filter(name=STANDARD).exclude(
        additional_price=0, additional_child_price=0
    )
    count = nonzero.count()
    if not count:
        return
    sample = list(
        nonzero.values_list(
            "id", "trip_id", "additional_price", "additional_child_price"
        )[:20]
    )
    print(
        f"\n[0008_backfill_standard_trip_package] WARNING: {count} existing "
        "STANDARD TripPackage row(s) have a non-zero additional_price/"
        "additional_child_price. Left untouched by this backfill - review "
        f"manually (id, trip_id, additional_price, additional_child_price): "
        f"{sample}{' ...' if count > len(sample) else ''}\n"
    )


def backfill_standard_packages(apps, schema_editor):
    Trip = apps.get_model("django_trips", "Trip")
    TripPackage = apps.get_model("django_trips", "TripPackage")

    report_nonzero_standard_packages(TripPackage)

    trips_missing_standard = Trip.objects.exclude(packages__name=STANDARD)
    for trip in trips_missing_standard.iterator():
        TripPackage.objects.get_or_create(
            trip=trip,
            name=STANDARD,
            defaults={"additional_price": 0, "additional_child_price": 0},
        )


def noop_reverse(apps, schema_editor):
    """
    Irreversible by design: this migration can't tell which Standard
    packages it created vs. which already existed, so removing them on
    reverse could delete pre-existing, legitimately-priced rows.
    """


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0007_rename_trippackage_price_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_standard_packages, noop_reverse),
    ]
