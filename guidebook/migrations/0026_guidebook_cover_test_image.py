# Generated by Django 3.0.3 on 2020-09-18 17:13

from django.db import migrations, models
import guidebook.models
import storages.backends.s3boto3
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('guidebook', '0025_auto_20200915_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='guidebook',
            name='cover_test_image',
            field=models.ImageField(null=True, storage=storages.backends.s3boto3.S3Boto3Storage(bucket=settings.AWS_STORAGE_BUCKET_NAME), upload_to=guidebook.models.image_directory_path),
        ),
    ]