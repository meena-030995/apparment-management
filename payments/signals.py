from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.notifications import (
    send_payment_created_notifications,
    send_payment_paid_notifications,
)

from .models import Payment


@receiver(pre_save, sender=Payment)
def capture_previous_payment_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        Payment.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    )


@receiver(post_save, sender=Payment)
def send_payment_notifications(sender, instance, created, **kwargs):
    if created:
        send_payment_created_notifications(
            instance,
            source=getattr(instance, "_notification_source", "system"),
        )
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status != "paid" and instance.status == "paid":
        send_payment_paid_notifications(instance)
