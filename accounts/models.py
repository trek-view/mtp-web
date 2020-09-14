from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
from datetime import datetime
# Create your models here.

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

def image_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user/{}'.format(instance.username)

class CustomUser(AbstractUser):
    # username = None
    email = models.EmailField(_('email address'), unique=True)
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed for Username.')
    alpha = RegexValidator(r'^[a-zA-Z]*$', 'Only alpha characters are allowed for Username.')
    username = models.CharField(max_length=100, unique=True, validators=[alphanumeric])
    is_active = models.BooleanField(default=False)
    is_maillist = models.BooleanField(default=False)
    mapillary_access_token = models.TextField(default='', null=True, blank=True)
    verify_email_key = models.CharField(max_length=100, default='')

    avatar = models.ImageField(upload_to=image_directory_path, null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True, validators=[alpha])
    last_name = models.CharField(max_length=30, null=True, blank=True, validators=[alpha])
    website_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.username
        # return self.email

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self._password is not None:
            password_validation.password_changed(self._password, self)
            self._password = None

class MapillaryUser(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, null=True)
    key = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=100, null=True)
    avatar = models.CharField(max_length=255, null=True)
    about = models.TextField(null=True)
    created_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    iamges_total_count = models.IntegerField(default=0)
    sequences_total_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)