# Generated by Django 3.0.3 on 2020-12-24 15:51

from django.db import migrations, models
import guidebook.models
import storages.backends.s3boto3


class Migration(migrations.Migration):

    dependencies = [
        ('guidebook', '0014_auto_20201224_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pointofinterest',
            name='image',
            field=models.ImageField(blank=True, max_length=255, null=True, storage=storages.backends.s3boto3.S3Boto3Storage(bucket='staging-backpack.mtp.trekview.org'), upload_to=guidebook.models.poi_image_directory_path),
        ),
        migrations.AlterField(
            model_name='scene',
            name='image',
            field=models.ImageField(blank=True, max_length=255, null=True, storage=storages.backends.s3boto3.S3Boto3Storage(bucket='staging-backpack.mtp.trekview.org'), upload_to=guidebook.models.scene_image_directory_path),
        ),
    ]
