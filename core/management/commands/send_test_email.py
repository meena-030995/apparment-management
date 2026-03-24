from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail


class Command(BaseCommand):
    help = "Send a test email using the current Django SMTP settings."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Recipient email address.")

    def handle(self, *args, **options):
        recipient = options["recipient"]

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError(
                "EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is missing. "
                "Set them in environment variables or in the project .env file."
            )

        try:
            send_mail(
                subject="Apartment Management test email",
                message=(
                    "This is a test email from your Django apartment management project. "
                    "If you received this, SMTP is configured correctly."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f"Email send failed: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(f"Test email sent successfully to {recipient}.")
        )
