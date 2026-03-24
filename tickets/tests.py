from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from .models import Ticket


class TicketAdminNavigationTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_tickets",
            password="testpass123",
            role="admin",
            phone="9999999999",
            is_approved=True,
        )
        self.ticket = Ticket.objects.create(
            resident=self.admin_user,
            title="Leakage",
            description="Tap is leaking",
            category="plumbing",
            status="assigned",
        )

    def test_all_tickets_page_has_dashboard_link(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("all_tickets"))

        self.assertContains(response, reverse("dashboard"))

    def test_update_ticket_page_has_navigation_and_selected_status(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("update_ticket", args=[self.ticket.id]))

        self.assertContains(response, reverse("all_tickets"))
        self.assertContains(response, reverse("dashboard"))
        self.assertContains(response, 'option value="assigned" selected', html=False)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TicketNotificationTests(TestCase):
    def test_ticket_creation_sends_resident_and_staff_notifications(self):
        resident = User.objects.create_user(
            username="resident_ticket_notify",
            password="testpass123",
            role="resident",
            phone="1111111111",
            email="resident@example.com",
            is_approved=True,
        )
        User.objects.create_user(
            username="staff_ticket_notify",
            password="testpass123",
            role="staff",
            phone="2222222222",
            email="staff@example.com",
            is_approved=True,
        )

        Ticket.objects.create(
            resident=resident,
            title="Ceiling leak",
            description="Water is dripping in the kitchen.",
            category="plumbing",
        )

        self.assertEqual(len(mail.outbox), 2)
        recipients = sorted(tuple(message.to) for message in mail.outbox)
        self.assertEqual(
            recipients,
            [("resident@example.com",), ("staff@example.com",)],
        )
        self.assertEqual(mail.outbox[0].subject, "Ticket Raised Confirmation")
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
