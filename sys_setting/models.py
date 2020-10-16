from django.db import models
from django.core.validators import RegexValidator
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
