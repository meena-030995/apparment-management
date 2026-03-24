from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    HOUSEHOLD_TYPE_CHOICES = (
        ("bachelor", "Bachelor"),
        ("family", "Family"),
    )

    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('security', 'Security'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    flat = models.ForeignKey(
        "flats.Flat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residents",
    )
    id_proof = models.FileField(upload_to="resident_proofs/id/", null=True, blank=True)
    address_proof = models.FileField(
        upload_to="resident_proofs/address/",
        null=True,
        blank=True,
    )
    household_type = models.CharField(
        max_length=20,
        choices=HOUSEHOLD_TYPE_CHOICES,
        default="family",
    )
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Keep Django auth flags aligned with the app-specific role.
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
            self.is_approved = True
        elif self.role == 'staff':
            self.is_staff = True
            self.is_superuser = False
            self.is_approved = True
        elif self.role == 'security':
            self.is_staff = False
            self.is_superuser = False
            self.is_approved = True
        elif self.role == 'resident':
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('ticket_created', 'Ticket Created'),
        ('ticket_updated', 'Ticket Updated'),
        ('visitor_added', 'Visitor Added'),
        ('visitor_exited', 'Visitor Exited'),
        ('notice_created', 'Notice Created'),
        ('payment_created', 'Payment Created'),
        ('payment_paid', 'Payment Paid'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"


class FamilyMember(models.Model):
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )

    resident = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="family_members",
    )
    name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    relationship = models.CharField(max_length=80, blank=True)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]

    def save(self, *args, **kwargs):
        today = timezone.localdate()
        self.age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.resident.username})"
