from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass123")
        self.client.login(username="alice", password="pass123")

    def test_update_profile_page(self):
        url = reverse("users:profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")