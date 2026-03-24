
# Create your models here.
from django.db import models
from django.conf import settings


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ("maintenance", "Maintenance"),
        ("water", "Water"),
        ("other", "Other"),
    )

    GATEWAY_CHOICES = (
        ("manual", "Manual"),
        ("razorpay", "Razorpay"),
        ("stripe", "Stripe"),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    )

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    month = models.CharField(max_length=20,null=True, blank=True)

    year = models.IntegerField(null=True, blank=True)

    due_date = models.DateField(null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default="maintenance",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    gateway = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES,
        default="razorpay",
    )

    payment_method = models.CharField(max_length=50, blank=True)

    transaction_id = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    gateway_order_id = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resident} - {self.month} {self.year}"
