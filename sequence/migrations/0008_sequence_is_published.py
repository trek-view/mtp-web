# Generated by Django 3.0.3 on 2020-08-18 00:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0007_sequence_is_mapillary'),
    ]

    operations = [
        migrations.AddField(
            model_name='sequence',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
    ]