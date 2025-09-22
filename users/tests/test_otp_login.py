from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPLoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bob", 
            phone_number="09123456789", 
            password="testpass",
            first_name="Bob",
            last_name="Smith",
            ssn="1234567890"
        )
        self.user.is_active = True
        self.user.save()

    def test_form_valid_redirects(self):
        url = reverse("users:otp_login")
        response = self.client.post(url, {"phone_number": "09123456789"})
        self.assertRedirects(response, reverse("users:verify_phone"))
        self.assertEqual(self.client.session["phone_number"], "09123456789")