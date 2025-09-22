from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class LogoutViewTest(TestCase):
    """Test logout functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='patient',
            first_name='Test',
            last_name='User',
            ssn='1234567890',
            phone_number='09123456789'
        )
    
    def test_logout_get_request(self):
        """Test that logout works with GET request"""
        # Login the user
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET logout
        response = self.client.get(reverse('users:logout'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:login'))
    
    def test_logout_post_request(self):
        """Test that logout works with POST request"""
        # Login the user
        self.client.login(username='testuser', password='testpass123')
        
        # Test POST logout
        response = self.client.post(reverse('users:logout'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:login'))
    
    def test_logout_redirects_to_login(self):
        """Test that logout redirects to login page"""
        # Login the user
        self.client.login(username='testuser', password='testpass123')
        
        # Test logout
        response = self.client.get(reverse('users:logout'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:login'))
