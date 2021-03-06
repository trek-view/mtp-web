# Generated by Django 3.1.2 on 2020-10-20 09:40

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0014_mapfeature'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapfeature',
            name='detection_keys',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), size=None), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='mapfeature',
            name='image_keys',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), size=None), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='mapfeature',
            name='user_keys',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), size=None), blank=True, null=True, size=None),
        ),
    ]
