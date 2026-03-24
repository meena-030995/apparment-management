from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Visitor


class VisitorExitAccessTests(TestCase):
    def setUp(self):
        self.security_user = User.objects.create_user(
            username="security_exit",
            password="testpass123",
            role="security",
            phone="6666666666",
            is_approved=True,
        )
        self.resident_user = User.objects.create_user(
            username="resident_exit",
            password="testpass123",
            role="resident",
            phone="7777777777",
            is_approved=True,
        )
        self.visitor = Visitor.objects.create(
            name="Visitor One",
            phone="8888888888",
            flat_number="A-101",
            vehicle_registration_number="TN-01-AB-1234",
            purpose="Delivery",
            security=self.security_user,
        )

    def test_get_visitor_exit_does_not_update_exit_time(self):
        self.client.force_login(self.security_user)

        response = self.client.get(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("visitor_list"))
        self.visitor.refresh_from_db()
        self.assertIsNone(self.visitor.exit_time)

    def test_resident_cannot_mark_visitor_exit(self):
        self.client.force_login(self.resident_user)

        response = self.client.post(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("dashboard"))
        self.visitor.refresh_from_db()
        self.assertIsNone(self.visitor.exit_time)

    def test_security_can_mark_visitor_exit(self):
        self.client.force_login(self.security_user)

        response = self.client.post(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("visitor_list"))
        self.visitor.refresh_from_db()
        self.assertIsNotNone(self.visitor.exit_time)


class VisitorRoleAccessTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_visitor",
            password="testpass123",
            role="admin",
            phone="1010101010",
            is_approved=True,
        )
        self.staff_user = User.objects.create_user(
            username="staff_visitor",
            password="testpass123",
            role="staff",
            phone="2020202020",
            is_approved=True,
        )
        self.security_user = User.objects.create_user(
            username="security_visitor",
            password="testpass123",
            role="security",
            phone="3030303030",
            is_approved=True,
        )

    def test_admin_cannot_open_add_visitor_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("add_visitor"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_staff_can_view_visitor_list(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("visitor_list"))

        self.assertEqual(response.status_code, 200)

    def test_security_can_open_add_visitor_form(self):
        self.client.force_login(self.security_user)

        response = self.client.get(reverse("add_visitor"))

        self.assertEqual(response.status_code, 200)

    def test_visitor_list_shows_vehicle_registration_number(self):
        Visitor.objects.create(
            name="Visitor Two",
            phone="9090909090",
            flat_number="B-202",
            vehicle_registration_number="KA-05-MN-9876",
            purpose="Guest",
            security=self.security_user,
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("visitor_list"))

        self.assertContains(response, "Vehicle No.")
        self.assertContains(response, "KA-05-MN-9876")
