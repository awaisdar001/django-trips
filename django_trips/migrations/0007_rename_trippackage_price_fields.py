from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_trips", "0006_rename_tripoption_trippackage"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trippackage",
            old_name="base_price",
            new_name="additional_price",
        ),
        migrations.RenameField(
            model_name="trippackage",
            old_name="base_child_price",
            new_name="additional_child_price",
        ),
        migrations.AlterModelOptions(
            name="trippackage",
            options={"ordering": ["trip", "additional_price"]},
        ),
    ]
