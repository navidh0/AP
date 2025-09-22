from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from doctor.models import Doctor

User = get_user_model()


class DoctorReverificationTest(TestCase):
    """Test re-verification of rejected doctors"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            first_name='Admin',
            last_name='User',
            ssn='1234567890',
            phone_number='09123456789',
            is_staff=True,
            is_superuser=True
        )
        
        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='test@doctor.com',
            password='testpass123',
            role='doctor',
            first_name='Test',
            last_name='Doctor',
            ssn='1234567891',
            phone_number='09123456790'
        )
        
        # Get doctor profile (created by signal)
        self.doctor = self.doctor_user.doctor_profile
        
        # Login as admin
        self.client.login(username='admin', password='adminpass123')
    
    def test_reject_doctor(self):
        """Test rejecting a doctor"""
        # Initially pending
        self.assertEqual(self.doctor.verification_status, 'pending')
        
        # Reject the doctor directly using the model method
        success = self.doctor.reject_verification(self.admin_user, "Test rejection")
        self.assertTrue(success)
        
        # Check status
        self.assertEqual(self.doctor.verification_status, 'rejected')
        self.assertFalse(self.doctor.is_verified)
    
    def test_reverify_rejected_doctor(self):
        """Test re-verifying a rejected doctor"""
        # First reject the doctor
        self.doctor.reject_verification(self.admin_user, "Test rejection")
        self.assertEqual(self.doctor.verification_status, 'rejected')
        
        # Now re-verify using the model method
        success = self.doctor.verify(self.admin_user, "Re-verification")
        self.assertTrue(success)
        
        # Check status
        self.assertEqual(self.doctor.verification_status, 'verified')
        self.assertTrue(self.doctor.is_verified)
    
    def test_cannot_verify_suspended_doctor(self):
        """Test that suspended doctors cannot be verified"""
        # Suspend the doctor
        self.doctor.suspend(self.admin_user, "Test suspension")
        self.assertEqual(self.doctor.verification_status, 'suspended')
        
        # Try to verify using the model method
        success = self.doctor.verify(self.admin_user, "Should not work")
        self.assertFalse(success)
        
        # Should still be suspended
        self.assertEqual(self.doctor.verification_status, 'suspended')
        self.assertFalse(self.doctor.is_verified)