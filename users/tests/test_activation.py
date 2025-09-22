from django.test import TestCase
from django.urls import reverse
from django.core import signing
from django.contrib.auth import get_user_model

User = get_user_model()

class ActivationViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "john",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "1234567890",
            "ssn": "123-45-6789",
            "role": "user",
            "password1": "StrongPass123!"
        }

    def test_valid_token_creates_user(self):
        token = signing.dumps(self.user_data, salt="user-activation")
        url = reverse("users:activate", kwargs={"token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="john").exists())

    def test_invalid_token(self):
        url = reverse("users:activate", kwargs={"token": "badtoken"})
        response = self.client.get(url)
        self.assertContains(response, "Invalid Activation Link")