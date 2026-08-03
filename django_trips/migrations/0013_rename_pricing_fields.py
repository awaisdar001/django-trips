"""
Schema-only half of the pricing model reversal (see docs/TripPricingModelReversalPlan.md
in the destipak root repo). Mirrors the 0007 (rename) -> 0012 (data recompute)
split already established in this app's own history - do not conflate the
rename with the data recompute 0014 does, and do not repeat 0007's original
mistake of renaming a field without recalculating its stored value.

TripPackage.additional_price/additional_child_price (a delta on top of
TripSchedule.price) become base_price/base_child_price (an absolute per-tier
price again). TripSchedule.price/child_price (the absolute per-date price)
become additional_price/additional_child_price (a flat surcharge added on
top of whichever package tier is booked). After this migration the columns
are renamed but the *values* still reflect the old semantics - 0014 rebases
them.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0012_normalize_trippackage_deltas"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trippackage",
            old_name="additional_price",
            new_name="base_price",
        ),
        migrations.RenameField(
            model_name="trippackage",
            old_name="additional_child_price",
            new_name="base_child_price",
        ),
        migrations.AlterModelOptions(
            name="trippackage",
            options={"ordering": ["trip", "base_price"]},
        ),
        migrations.RenameField(
            model_name="tripschedule",
            old_name="price",
            new_name="additional_price",
        ),
        migrations.RenameField(
            model_name="tripschedule",
            old_name="child_price",
            new_name="additional_child_price",
        ),
    ]
