from django.test import TestCase
from django.urls import reverse

class VerifyPhoneTest(TestCase):
    def test_redirect_if_no_session_phone(self):
        url = reverse("users:verify_phone")
        response = self.client.post(url, {"otp_code": "123456"})
        self.assertRedirects(response, reverse("users:otp_login"))