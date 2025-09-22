from django.test import TestCase
from django.urls import reverse

class ResendActivationTest(TestCase):
    def test_redirect_if_no_data(self):
        url = reverse("users:resend_activation")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("users:signup"))