from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0014_rebase_absolute_prices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tripschedule",
            name="additional_child_price",
            field=models.DecimalField(
                decimal_places=0,
                default=0,
                help_text="Flat per-child surcharge for this specific departure "
                "date (e.g. weekend/holiday/peak pricing), added on top of "
                "whichever package tier is booked - same flat-addition semantic "
                "as TripPickupLocation.additional_price. 0 for a regular date.",
                max_digits=7,
            ),
        ),
    ]
