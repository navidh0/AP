from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Notification
from doctor.models import Doctor, DayOff, ProfileChangeRequest
from wallet.models import Wallet, FundingRequest
from booking.models import Appointment, Timeslot

User = get_user_model()


class AdminDashboardTest(TestCase):
    """Test cases for admin dashboard functionality"""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='0000000001',
            phone_number='09111111111'
        )
        self.admin_user.is_active = True
        self.admin_user.save()
        
        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='Dr. John',
            last_name='Doe',
            ssn='0000000002',
            phone_number='09222222222'
        )
        self.doctor_user.is_active = True
        self.doctor_user.save()
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='0000000003',
            phone_number='09333333333'
        )
        self.patient_user.is_active = True
        self.patient_user.save()
        self.wallet = Wallet.objects.create(user=self.patient_user, balance=100.00)
        
        self.client = Client()
    
    def test_admin_dashboard_access_requires_staff(self):
        """Test that admin dashboard requires staff access"""
        # Login as non-staff user
        self.client.force_login(self.doctor_user)
        url = reverse('admin_dashboard:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_admin_dashboard_access_with_staff(self):
        """Test that admin dashboard is accessible with staff access"""
        # Login as admin user
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')
    
    def test_admin_dashboard_context_data(self):
        """Test that admin dashboard has correct context data"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
        
        stats = response.context['stats']
        self.assertEqual(stats['total_patients'], 1)
        self.assertEqual(stats['total_doctors'], 1)
        self.assertEqual(stats['total_appointments'], 0)
        self.assertEqual(stats['pending_funding_requests'], 0)
        self.assertEqual(stats['pending_doctor_verifications'], 1)


class DoctorVerificationTest(TestCase):
    """Test cases for doctor verification functionality"""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin2',
            last_name='User',
            ssn='0000000004',
            phone_number='09444444444'
        )
        self.admin_user.is_active = True
        self.admin_user.save()
        
        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor2',
            email='doctor2@example.com',
            password='testpass123',
            role='doctor',
            first_name='Dr. Jane',
            last_name='Smith',
            ssn='0000000005',
            phone_number='09555555555'
        )
        self.doctor_user.is_active = True
        self.doctor_user.save()
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        self.client = Client()
    
    def test_verify_doctor(self):
        """Test verifying a doctor"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:verify_doctor', kwargs={'doctor_id': self.doctor.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Verified after document review'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_dashboard:manage_doctors'))
        
        # Check if doctor was verified
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.verification_status, 'verified')
        self.assertTrue(self.doctor.is_verified)
    
    def test_reject_doctor(self):
        """Test rejecting a doctor"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:reject_doctor', kwargs={'doctor_id': self.doctor.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Insufficient documentation'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check if doctor was rejected
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.verification_status, 'rejected')
        self.assertFalse(self.doctor.is_verified)
    
    def test_suspend_doctor(self):
        """Test suspending a doctor"""
        # First verify the doctor
        self.doctor.verify(self.admin_user)
        
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:suspend_doctor', kwargs={'doctor_id': self.doctor.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Suspended due to complaints'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check if doctor was suspended
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.verification_status, 'suspended')
        self.assertFalse(self.doctor.is_verified)
    
    def test_toggle_doctor_availability(self):
        """Test toggling doctor availability"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:toggle_doctor_availability', kwargs={'doctor_id': self.doctor.id})
        
        # Initially available
        self.assertTrue(self.doctor.availability)
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Should be unavailable now
        self.doctor.refresh_from_db()
        self.assertFalse(self.doctor.availability)


class FundingRequestManagementTest(TestCase):
    """Test cases for funding request management"""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin3',
            email='admin3@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin3',
            last_name='User',
            ssn='0000000006',
            phone_number='09666666666'
        )
        self.admin_user.is_active = True
        self.admin_user.save()
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient2',
            email='patient2@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane2',
            last_name='Smith',
            ssn='0000000007',
            phone_number='09777777777'
        )
        self.patient_user.is_active = True
        self.patient_user.save()
        self.wallet = Wallet.objects.create(user=self.patient_user, balance=50.00)
        
        # Create funding request
        self.funding_request = FundingRequest.objects.create(
            user=self.patient_user,
            amount=100.00,
            description='Test funding request'
        )
        
        self.client = Client()
    
    def test_approve_funding_request(self):
        """Test approving a funding request"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:approve_funding_request', kwargs={'request_id': self.funding_request.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Approved for testing'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check if funding request was approved
        self.funding_request.refresh_from_db()
        self.assertEqual(self.funding_request.status, 'approved')
        self.assertEqual(self.funding_request.processed_by, self.admin_user)
        
        # Check if wallet balance was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 150.00)  # 50 + 100
    
    def test_reject_funding_request(self):
        """Test rejecting a funding request"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:reject_funding_request', kwargs={'request_id': self.funding_request.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Insufficient documentation'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check if funding request was rejected
        self.funding_request.refresh_from_db()
        self.assertEqual(self.funding_request.status, 'rejected')
        self.assertEqual(self.funding_request.processed_by, self.admin_user)
        
        # Check if wallet balance remains unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 50.00)


class NotificationIntegrationTest(TestCase):
    """Test cases for notification integration with admin actions"""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin4',
            email='admin4@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin4',
            last_name='User',
            ssn='0000000008',
            phone_number='09888888888'
        )
        self.admin_user.is_active = True
        self.admin_user.save()
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient3',
            email='patient3@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane3',
            last_name='Smith',
            ssn='0000000009',
            phone_number='09999999999'
        )
        self.patient_user.is_active = True
        self.patient_user.save()
        self.wallet = Wallet.objects.create(user=self.patient_user, balance=50.00)
        
        # Create funding request
        self.funding_request = FundingRequest.objects.create(
            user=self.patient_user,
            amount=100.00,
            description='Test funding request'
        )
        
        self.client = Client()
    
    def test_notification_created_on_funding_approval(self):
        """Test that notification is created when funding request is approved"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:approve_funding_request', kwargs={'request_id': self.funding_request.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Approved for testing'
        })
        
        # Check if notification was created
        notification = Notification.objects.filter(
            user=self.patient_user,
            notification_type='wallet_funding_approved'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, 'Funding Request Approved')
        self.assertIn('$100.00', notification.message)
    
    def test_notification_created_on_funding_rejection(self):
        """Test that notification is created when funding request is rejected"""
        self.client.force_login(self.admin_user)
        url = reverse('admin_dashboard:reject_funding_request', kwargs={'request_id': self.funding_request.id})
        
        response = self.client.post(url, {
            'admin_notes': 'Insufficient documentation'
        })
        
        # Check if notification was created
        notification = Notification.objects.filter(
            user=self.patient_user,
            notification_type='wallet_funding_rejected'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, 'Funding Request Rejected')
        self.assertIn('Insufficient documentation', notification.message)
