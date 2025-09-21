from django.test import TestCase
from django.urls import reverse

class LoginViewTest(TestCase):
    def test_login_page_renders(self):
        url = reverse("users:login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")