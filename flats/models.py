from django.db import models

# Create your models here.


class Block(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Flat(models.Model):

    block = models.CharField(max_length=10)
    number = models.CharField(max_length=10)
    floor = models.IntegerField(default=0)

    class Meta:
        ordering = ["block", "number"]
        unique_together = ("block", "number")

    def __str__(self):
        return f"{self.block}-{self.number}"
