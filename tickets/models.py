
# # Create your models here.
# from django.db import models
# from django.conf import settings


# class Ticket(models.Model):

#     STATUS = (
#         ('open', 'Open'),
#         ('assigned', 'Assigned'),
#         ('in_progress', 'In Progress'),
#         ('closed', 'Closed')
#     )

#     resident = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

#     title = models.CharField(max_length=200)
#     description = models.TextField()

#     status = models.CharField(max_length=20, choices=STATUS, default='open')

#     created_at = models.DateTimeField(auto_now_add=True)
    
    
from django.db import models
from django.conf import settings


class Ticket(models.Model):

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    )

    CATEGORY_CHOICES = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('security', 'Security'),
        ('other', 'Other')
    )

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open"
    )

    image = models.ImageField(upload_to="tickets/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title