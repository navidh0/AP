from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordChangeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
            ssn="1234567890",
            phone_number="09123456789"
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username="testuser", password="testpass123")
    
    def test_change_page_renders(self):
        url = reverse("users:password_change")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)