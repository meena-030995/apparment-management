from django.db.models.signals import post_save
from django.dispatch import receiver

from core.notifications import send_ticket_created_notifications

from .models import Ticket


@receiver(post_save, sender=Ticket)
def send_ticket_notifications(sender, instance, created, **kwargs):
    if created:
        send_ticket_created_notifications(instance)
