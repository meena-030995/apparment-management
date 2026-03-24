from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .services import generate_chat_reply


class AssistantViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="resident_ai",
            email="resident@example.com",
            password="Testpass123!",
            role="resident",
            phone="9876543210",
            is_approved=True,
        )

    def test_chat_page_requires_login(self):
        response = self.client.get(reverse("assistant_chat"))
        self.assertEqual(response.status_code, 302)

    def test_chat_page_renders_for_logged_in_user(self):
        self.client.login(username="resident_ai", password="Testpass123!")
        response = self.client.get(reverse("assistant_chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Apartment Assistant")

    @override_settings(OPENAI_API_KEY="")
    def test_chat_api_uses_local_fallback_without_configuration(self):
        self.client.login(username="resident_ai", password="Testpass123!")
        response = self.client.post(
            reverse("assistant_chat_api"),
            data='{"message": "How do notices work in this system?"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Notice Board", response.json()["reply"])

    @patch("ai_assistant.views.generate_chat_reply", return_value="You can raise a ticket from the dashboard.")
    def test_chat_api_returns_reply(self, mocked_generate_reply):
        self.client.login(username="resident_ai", password="Testpass123!")
        response = self.client.post(
            reverse("assistant_chat_api"),
            data='{"message": "How do I create a ticket?", "history": []}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["reply"],
            "You can raise a ticket from the dashboard.",
        )
        mocked_generate_reply.assert_called_once()


class AssistantServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="resident_service_ai",
            email="resident-service@example.com",
            password="Testpass123!",
            role="resident",
            phone="9876500000",
            is_approved=True,
        )

    @override_settings(OPENAI_API_KEY="test-key")
    @patch("ai_assistant.services.OpenAI", create=True)
    def test_generate_chat_reply_falls_back_when_openai_client_fails(self, mocked_openai):
        mocked_openai.return_value.responses.create.side_effect = RuntimeError("API down")

        reply = generate_chat_reply(
            self.user,
            "How do I pay dues?",
            history=[{"role": "user", "content": "hello"}],
        )

        self.assertIn("Maintenance Dues", reply)

    @override_settings(OPENAI_API_KEY="")
    def test_generate_chat_reply_ignores_invalid_history_items(self):
        reply = generate_chat_reply(
            self.user,
            "How do notices work?",
            history=["bad-item", 123, {"role": "user", "content": "hi"}],
        )

        self.assertIn("Notice Board", reply)
