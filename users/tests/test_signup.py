from django.test import TestCase
from django.urls import reverse

class SignUpViewTest(TestCase):
    def test_signup_stores_session(self):
        url = reverse("users:signup")
        response = self.client.post(url, {
            "username": "testuser",
            "email": "t@t.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
            "ssn": "1234567890",
            "phone_number": "09123456789",
            "role": "patient"
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("pending_user_data", self.client.session)