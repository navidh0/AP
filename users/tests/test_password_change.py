from django.test import TestCase
from django.urls import reverse

class PasswordChangeViewTest(TestCase):
    def test_change_page_renders(self):
        url = reverse("users:password_change")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)