from django.test import TestCase
from django.urls import reverse

class ResendOTPTest(TestCase):
    def test_redirect_if_no_phone(self):
        url = reverse("users:resend_otp")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("users:otp_login"))