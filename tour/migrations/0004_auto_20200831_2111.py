# Generated by Django 3.0.3 on 2020-08-31 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tour', '0003_auto_20200831_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tourtag',
            name='name',
            field=models.CharField(max_length=50, null=True, unique=True),
        ),
    ]
