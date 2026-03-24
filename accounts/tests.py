from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from flats.models import Block, Flat
from .models import ActivityLog, FamilyMember, User


class RegisterViewTests(TestCase):
    def setUp(self):
        self.block = Block.objects.create(name="A")

    def test_valid_registration_redirects_to_login(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newresident",
                "email": "newresident@example.com",
                "phone": "9999999999",
                "role": "resident",
                "block": self.block.id,
                "flat_number": "101",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newresident")
        self.assertEqual(user.email, "newresident@example.com")
        self.assertFalse(user.is_approved)
        self.assertIsNotNone(user.flat)
        self.assertEqual(user.flat.block, "A")
        self.assertEqual(user.flat.number, "101")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_registration_sends_welcome_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "welcomeuser",
                "email": "welcome@example.com",
                "phone": "9999999998",
                "role": "resident",
                "block": self.block.id,
                "flat_number": "101",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Registration / Account Created")
        self.assertIn("Welcome to AMS", mail.outbox[0].body)
        self.assertIn("Temporary Password: testpass123", mail.outbox[0].body)
        self.assertIn("Flat No: 101", mail.outbox[0].body)
        self.assertIn("Block/Unit: A", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn("Account Created", mail.outbox[0].alternatives[0][0])

    def test_authenticated_user_is_redirected_from_register(self):
        user = User.objects.create_user(
            username="existinguser",
            password="testpass123",
            role="staff",
            phone="0000000000",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("register"))

        self.assertRedirects(response, reverse("dashboard"))


class DashboardViewTests(TestCase):
    def test_resident_dashboard_renders(self):
        user = User.objects.create_user(
            username="resident1",
            password="testpass123",
            role="resident",
            phone="1111111111",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/resident_dashboard.html")

    def test_resident_can_add_only_their_own_family_details(self):
        owner = User.objects.create_user(
            username="resident_owner",
            password="testpass123",
            role="resident",
            phone="1111111111",
            is_approved=True,
        )
        other = User.objects.create_user(
            username="resident_other",
            password="testpass123",
            role="resident",
            phone="9999999999",
            is_approved=True,
        )
        FamilyMember.objects.create(
            resident=other,
            name="Other Member",
            gender="female",
            relationship="Sister",
            date_of_birth="2000-01-01",
        )

        self.client.force_login(owner)
        response = self.client.post(
            reverse("dashboard"),
            {
                "family_action": "add",
                "household_type": "family",
                "name": "Anita Owner",
                "gender": "female",
                "relationship": "Spouse",
                "date_of_birth": "1995-05-14",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            FamilyMember.objects.filter(resident=owner, name="Anita Owner").exists()
        )
        self.assertContains(response, "Anita Owner")
        self.assertNotContains(response, "Other Member")

    def test_staff_dashboard_shows_household_details(self):
        staff_user = User.objects.create_user(
            username="staff1",
            password="testpass123",
            role="staff",
            phone="3333333333",
            is_approved=True,
        )
        resident = User.objects.create_user(
            username="resident_family",
            password="testpass123",
            role="resident",
            phone="4444444444",
            is_approved=True,
            household_type="family",
        )
        FamilyMember.objects.create(
            resident=resident,
            name="Ravi Kumar",
            gender="male",
            relationship="Father",
            date_of_birth="1980-06-21",
        )

        self.client.force_login(staff_user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_dashboard.html")
        self.assertContains(response, "Ravi Kumar")
        self.assertContains(response, "Family")

    def test_admin_dashboard_shows_household_details(self):
        admin_user = User.objects.create_user(
            username="admin1",
            password="testpass123",
            role="admin",
            phone="5555555555",
            is_approved=True,
        )
        resident = User.objects.create_user(
            username="resident_bachelor",
            password="testpass123",
            role="resident",
            phone="6666666666",
            is_approved=True,
            household_type="bachelor",
        )
        FamilyMember.objects.create(
            resident=resident,
            name="Solo Resident",
            gender="male",
            relationship="Self",
            date_of_birth="1998-03-18",
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin_dashboard.html")
        self.assertContains(response, "Solo Resident")
        self.assertContains(response, "Bachelor")

    def test_security_dashboard_renders(self):
        user = User.objects.create_user(
            username="security1",
            password="testpass123",
            role="security",
            phone="2222222222",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/security_dashboard.html")

    def test_staff_dashboard_renders(self):
        user = User.objects.create_user(
            username="staff_render",
            password="testpass123",
            role="staff",
            phone="3333333333",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_dashboard.html")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class LoginNotificationTests(TestCase):
    def test_login_sends_email_and_logs_activity(self):
        user = User.objects.create_user(
            username="notify_login",
            password="testpass123",
            role="resident",
            phone="7777777777",
            email="notify@example.com",
            is_approved=True,
        )

        response = self.client.post(
            reverse("login"),
            {"username": "notify_login", "password": "testpass123"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["notify@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Login Notification")
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn("Login Alert", mail.outbox[0].alternatives[0][0])
        self.assertTrue(
            ActivityLog.objects.filter(user=user, action="login").exists()
        )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegisterAPINotificationTests(TestCase):
    def setUp(self):
        self.block = Block.objects.create(name="B")

    def test_register_api_sends_welcome_email(self):
        client = APIClient()

        response = client.post(
            reverse("api_register"),
            {
                "username": "apiwelcome",
                "email": "apiwelcome@example.com",
                "phone": "1234512345",
                "role": "resident",
                "block": self.block.id,
                "flat_number": "202",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Registration / Account Created")
        self.assertIn("Welcome to AMS", mail.outbox[0].body)
        self.assertIn("Flat No: 202", mail.outbox[0].body)
