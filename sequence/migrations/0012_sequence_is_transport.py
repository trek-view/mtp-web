# Generated by Django 3.0.3 on 2020-08-18 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0011_auto_20200818_0252'),
    ]

    operations = [
        migrations.AddField(
            model_name='sequence',
            name='is_transport',
            field=models.BooleanField(default=False),
        ),
    ]