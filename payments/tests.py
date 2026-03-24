from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from accounts.models import User
from .models import Payment
from .serializers import PaymentSerializer


class PaymentAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="resident_owner",
            password="testpass123",
            role="resident",
            phone="4444444444",
            is_approved=True,
        )
        self.other_user = User.objects.create_user(
            username="resident_other",
            password="testpass123",
            role="resident",
            phone="5555555555",
            is_approved=True,
        )
        self.payment = Payment.objects.create(
            resident=self.owner,
            month="March",
            year=2026,
            amount=Decimal("1500.00"),
            status="pending",
        )

    def test_get_pay_now_does_not_mark_payment_paid(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("pay_now", args=[self.payment.id]))

        self.assertRedirects(response, reverse("my_dues"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")
        self.assertFalse(self.payment.transaction_id)

    def test_user_cannot_pay_another_users_payment(self):
        self.client.force_login(self.other_user)

        response = self.client.post(reverse("pay_now", args=[self.payment.id]))

        self.assertEqual(response.status_code, 404)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_owner_can_pay_own_pending_payment(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("pay_now", args=[self.payment.id]))

        self.assertRedirects(response, reverse("payment_history"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "paid")
        self.assertTrue(self.payment.transaction_id)

    @override_settings(DEBUG=True, RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    def test_create_payment_uses_dev_fallback_when_gateway_not_configured(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("create_payment", args=[self.payment.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete Test Payment")

    @override_settings(DEBUG=False, RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    def test_create_payment_redirects_with_error_when_gateway_not_configured_in_production(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("create_payment", args=[self.payment.id]))

        self.assertRedirects(response, reverse("my_dues"))


class PaymentRecordsViewTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_payments",
            password="testpass123",
            role="admin",
            phone="9090909090",
            is_approved=True,
        )
        self.resident_user = User.objects.create_user(
            username="resident_payments",
            password="testpass123",
            role="resident",
            phone="8080808080",
            is_approved=True,
        )

    def test_admin_can_view_payment_records_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("payment_records"))

        self.assertEqual(response.status_code, 200)

    def test_non_admin_is_redirected_from_payment_records_page(self):
        self.client.force_login(self.resident_user)

        response = self.client.get(reverse("payment_records"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_admin_can_create_payment_record_from_page(self):
        resident = User.objects.create_user(
            username="resident_records",
            password="testpass123",
            role="resident",
            phone="7070707070",
            is_approved=True,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("payment_records"),
            {
                "resident": resident.id,
                "month": "June",
                "year": 2026,
                "due_date": "2026-06-10",
                "payment_type": "maintenance",
                "amount": "2450.00",
                "status": "pending",
                "gateway": "razorpay",
                "payment_method": "UPI",
                "transaction_id": "",
            },
        )

        self.assertRedirects(response, reverse("payment_records"))
        self.assertTrue(
            Payment.objects.filter(resident=resident, month="June", year=2026).exists()
        )

    def test_admin_can_update_payment_record_from_page(self):
        payment = Payment.objects.create(
            resident=self.resident_user,
            month="July",
            year=2026,
            amount=Decimal("1900.00"),
            status="pending",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("payment_records"),
            {
                "action": "update",
                "payment_id": payment.id,
                "resident": self.resident_user.id,
                "month": "July",
                "year": 2026,
                "due_date": "2026-07-15",
                "payment_type": "water",
                "amount": "2100.00",
                "status": "paid",
                "gateway": "manual",
                "payment_method": "Cash",
                "transaction_id": "txn_admin_edit",
            },
        )

        self.assertRedirects(response, reverse("payment_records"))
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("2100.00"))
        self.assertEqual(payment.status, "paid")
        self.assertEqual(str(payment.due_date), "2026-07-15")
        self.assertEqual(payment.payment_type, "water")
        self.assertEqual(payment.gateway, "manual")
        self.assertEqual(payment.payment_method, "Cash")
        self.assertEqual(payment.transaction_id, "txn_admin_edit")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PaymentNotificationTests(TestCase):
    def setUp(self):
        self.resident = User.objects.create_user(
            username="resident_payment_notify",
            password="testpass123",
            role="resident",
            phone="6666666666",
            email="resident-payment@example.com",
            is_approved=True,
        )
        self.admin = User.objects.create_user(
            username="admin_payment_notify",
            password="testpass123",
            role="admin",
            phone="7777777777",
            email="admin-payment@example.com",
            is_approved=True,
        )

    def test_payment_creation_sends_due_email(self):
        Payment.objects.create(
            resident=self.resident,
            month="March",
            year=2026,
            amount=Decimal("1800.00"),
            status="pending",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["resident-payment@example.com"])
        self.assertEqual(mail.outbox[0].subject, "New Due Created")
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")

    def test_marking_payment_paid_sends_resident_and_admin_emails(self):
        payment = Payment.objects.create(
            resident=self.resident,
            month="April",
            year=2026,
            amount=Decimal("1900.00"),
            status="pending",
        )
        mail.outbox = []

        payment.status = "paid"
        payment.transaction_id = "txn_123"
        payment.save()

        self.assertEqual(len(mail.outbox), 2)
        recipients = sorted(tuple(message.to) for message in mail.outbox)
        self.assertEqual(
            recipients,
            [("admin-payment@example.com",), ("resident-payment@example.com",)],
        )
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertEqual(mail.outbox[1].alternatives[0][1], "text/html")

    def test_api_payment_creation_uses_api_email_format(self):
        factory = APIRequestFactory()
        request = factory.post("/payments/api/create/")
        request.user = self.admin

        serializer = PaymentSerializer(
            data={
                "resident": self.resident.id,
                "month": "May",
                "year": 2026,
                "amount": "2100.00",
                "status": "pending",
            },
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "New Due Created via API")
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
