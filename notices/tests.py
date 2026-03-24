from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Notice


class NoticeCreationTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff_notice",
            password="testpass123",
            role="staff",
            phone="1212121212",
            is_approved=True,
        )
        self.resident_user = User.objects.create_user(
            username="resident_notice",
            password="testpass123",
            role="resident",
            phone="3434343434",
            is_approved=True,
        )

    def test_staff_can_create_notice(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("create_notice"),
            {
                "title": "Water Shutdown",
                "message": "Water supply will be unavailable from 10 AM to 1 PM.",
                "expiry_date": "2026-03-25",
            },
        )

        self.assertRedirects(response, reverse("notice_list"))
        self.assertTrue(Notice.objects.filter(title="Water Shutdown").exists())

    def test_invalid_notice_shows_errors(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("create_notice"),
            {
                "title": "",
                "message": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please correct the errors below.")

    def test_resident_cannot_create_notice(self):
        self.client.force_login(self.resident_user)

        response = self.client.get(reverse("create_notice"))

        self.assertRedirects(response, reverse("dashboard"))
