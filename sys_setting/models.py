from django.db import models
from django.core.validators import RegexValidator
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from django.contrib.auth import (
    get_user_model, )

UserModel = get_user_model()
# Create your models here.


class Tag(models.Model):
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed for Username.')
    name = models.CharField(max_length=50, unique=True, null=True, validators=[alphanumeric])
    description = models.TextField(default=None, blank=True, null=True)
    is_actived = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        print(self.name)
        super().save(*args, **kwargs)


def image_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'system/tier/business/{}'.format(instance.name)


class BusinessTier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.TextField(null=True)
    logo = models.ImageField(upload_to=image_directory_path, null=True, blank=True, storage=S3Boto3Storage(bucket=settings.AWS_STORAGE_BUCKET_NAME))


class GoldTier(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)


class SilverTier(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)

