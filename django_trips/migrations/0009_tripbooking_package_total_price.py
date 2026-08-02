import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0008_backfill_standard_trip_package"),
    ]

    operations = [
        migrations.AddField(
            model_name="tripbooking",
            name="package",
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text="Pricing package/tier selected for this booking. "
                "Defaults to the trip's Standard package when not supplied "
                "at creation time.",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bookings",
                to="django_trips.trippackage",
            ),
        ),
        migrations.AddField(
            model_name="tripbooking",
            name="total_price",
            field=models.DecimalField(
                default=0,
                max_digits=10,
                decimal_places=0,
                help_text="Computed total price for this booking (effective "
                "per-person price - schedule price + package delta + pickup "
                "surcharge - times number_of_persons), stored at creation time.",
            ),
        ),
    ]
