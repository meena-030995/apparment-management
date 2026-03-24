
# Create your models here.
from django.db import models
from django.conf import settings


class Visitor(models.Model):

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    flat_number = models.CharField(max_length=10)

    vehicle_registration_number = models.CharField(
        max_length=30,
        blank=True,
    )

    purpose = models.CharField(max_length=200)

    entry_time = models.DateTimeField(auto_now_add=True)

    exit_time = models.DateTimeField(null=True, blank=True)

    security = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} visiting {self.flat_number}"
