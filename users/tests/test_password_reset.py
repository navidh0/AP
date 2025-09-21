from django.test import TestCase
from django.urls import reverse

class PasswordResetViewTest(TestCase):
    def test_reset_page_renders(self):
        url = reverse("users:password_reset")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)