# Generated by Django 3.0.3 on 2020-08-17 08:29

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0005_sequence_geometry_coordinates_ary'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_actived', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='TransportType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='sequence',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='sequence',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='sequence',
            name='tag',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='0', max_length=6), null=True, size=None),
        ),
        migrations.AddField(
            model_name='sequence',
            name='transport_type',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='0', max_length=3), null=True, size=None),
        ),
    ]