# Generated by Django 2.2.24 on 2021-08-18 11:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('django_trips', '0004_auto_20210810_1559'), ('django_trips', '0005_auto_20210815_1724'), ('django_trips', '0006_auto_20210815_1754'), ('django_trips', '0007_auto_20210815_1818'), ('django_trips', '0008_auto_20210815_1830'), ('django_trips', '0009_auto_20210815_1832')]

    dependencies = [
        ('django_trips', '0003_auto_20210810_0940'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['slug'], name='django_trip_slug_a2c8a8_idx'),
        ),
        migrations.AddConstraint(
            model_name='location',
            constraint=models.UniqueConstraint(fields=('slug',), name='unique_slug_for_location'),
        ),
        migrations.CreateModel(
            name='HostType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_count', models.SmallIntegerField(blank=True, default=0, null=True)),
                ('rated_by', models.SmallIntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TripAvailability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('availability', models.CharField(choices=[('DL', 'Daily'), ('WK', 'Weekly'), ('MN', 'Monthly'), ('FD', 'FixDate')], default='MN', max_length=2)),
                ('options', models.CharField(blank=True, max_length=5, null=True)),
            ],
        ),
        migrations.RemoveConstraint(
            model_name='location',
            name='unique_slug_for_location',
        ),
        migrations.RenameField(
            model_name='trip',
            old_name='category',
            new_name='primary_category',
        ),
        migrations.RemoveField(
            model_name='trip',
            name='departure',
        ),
        migrations.AddField(
            model_name='trip',
            name='categories',
            field=models.ManyToManyField(related_name='trip_categories', to='django_trips.Category'),
        ),
        migrations.AddField(
            model_name='trip',
            name='passenger_limit',
            field=models.SmallIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='price_bracket',
            field=models.CharField(choices=[('ST', 'Standard'), ('BG', 'Budget')], default='ST', max_length=2),
        ),
        migrations.AddField(
            model_name='trip',
            name='starting_location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trip_starting_location', to='django_trips.Location'),
        ),
        migrations.AddConstraint(
            model_name='location',
            constraint=models.UniqueConstraint(fields=('slug', 'is_destination', 'is_departure'), name='unique_slug_for_location'),
        ),
        migrations.AddField(
            model_name='tripavailability',
            name='trip',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_availabilities', to='django_trips.Trip'),
        ),
        migrations.AddField(
            model_name='host',
            name='rating',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='host_rating', to='django_trips.Rating'),
        ),
        migrations.AddField(
            model_name='host',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='host_type', to='django_trips.HostType'),
        ),
        migrations.RemoveConstraint(
            model_name='location',
            name='unique_slug_for_location',
        ),
        migrations.RemoveField(
            model_name='location',
            name='is_departure',
        ),
        migrations.RemoveField(
            model_name='location',
            name='is_destination',
        ),
        migrations.AddConstraint(
            model_name='location',
            constraint=models.UniqueConstraint(fields=('slug',), name='unique_slug_for_location'),
        ),
        migrations.CreateModel(
            name='HostRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_count', models.SmallIntegerField(blank=True, default=0, null=True)),
                ('rated_by', models.SmallIntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='host',
            name='rating',
        ),
        migrations.DeleteModel(
            name='Rating',
        ),
        migrations.AddField(
            model_name='hostrating',
            name='host',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='host_rating', to='django_trips.Host'),
        ),
    ]
