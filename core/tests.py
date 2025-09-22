from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Notification
from doctor.models import Doctor, Timeslot, DayOff
from booking.models import Appointment
from wallet.models import Wallet, Transaction, FundingRequest

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
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
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='appointment_booked',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'appointment_booked')
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='appointment_booked',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
    
    def test_notification_create_notification_classmethod(self):
        """Test the create_notification class method"""
        notification = Notification.create_notification(
            user=self.user,
            notification_type='wallet_funded',
            title='Wallet Funded',
            message='Your wallet has been funded'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'wallet_funded')
        self.assertEqual(notification.title, 'Wallet Funded')
        self.assertFalse(notification.is_read)


class DoctorModelTest(TestCase):
    """Test cases for Doctor model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567891',
            phone_number='09123456790'
        )
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialty='Cardiology',
            fee=100.00
        )
    
    def test_doctor_creation(self):
        """Test creating a doctor"""
        self.assertEqual(self.doctor.user, self.user)
        self.assertEqual(self.doctor.specialty, 'Cardiology')
        self.assertEqual(self.doctor.fee, 100.00)
        self.assertTrue(self.doctor.availability)
        self.assertEqual(self.doctor.rating, 0.0)
    
    def test_doctor_str_representation(self):
        """Test doctor string representation"""
        expected = f"Dr. {self.user.get_full_name()} - {self.doctor.specialty}"
        self.assertEqual(str(self.doctor), expected)
    
    def test_doctor_verification(self):
        """Test doctor verification process"""
        self.assertEqual(self.doctor.verification_status, 'pending')
        
        # Create admin user for verification
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='1234567896',
            phone_number='09123456795'
        )
        
        # Verify doctor
        self.doctor.verify(admin_user)
        self.assertEqual(self.doctor.verification_status, 'verified')
        self.assertTrue(self.doctor.is_verified)
    
    def test_doctor_rejection(self):
        """Test doctor rejection process"""
        # Create admin user for verification
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='1234567897',
            phone_number='09123456796'
        )
        
        self.doctor.verify(admin_user)  # First verify
        self.doctor.reject_verification(admin_user)
        self.assertEqual(self.doctor.verification_status, 'rejected')
        self.assertFalse(self.doctor.is_verified)
    
    def test_doctor_suspension(self):
        """Test doctor suspension process"""
        # Create admin user for verification
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='1234567898',
            phone_number='09123456797'
        )
        
        self.doctor.verify(admin_user)  # First verify
        self.doctor.suspend(admin_user)
        self.assertEqual(self.doctor.verification_status, 'suspended')
        self.assertFalse(self.doctor.is_verified)
    
    def test_doctor_availability_toggle(self):
        """Test toggling doctor availability"""
        self.assertTrue(self.doctor.availability)
        
        self.doctor.toggle_availability()
        self.assertFalse(self.doctor.availability)
        
        self.doctor.toggle_availability()
        self.assertTrue(self.doctor.availability)


class WalletModelTest(TestCase):
    """Test cases for Wallet model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='1234567892',
            phone_number='09123456791'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_wallet_creation(self):
        """Test creating a wallet"""
        self.assertEqual(self.wallet.user, self.user)
        self.assertEqual(self.wallet.balance, 100.00)
    
    def test_add_funds(self):
        """Test adding funds to wallet"""
        initial_balance = float(self.wallet.balance)
        amount = 50.00
        
        self.wallet.add_funds(amount)
        self.assertEqual(float(self.wallet.balance), initial_balance + amount)
    
    def test_deduct_funds_sufficient_balance(self):
        """Test deducting funds with sufficient balance"""
        initial_balance = float(self.wallet.balance)
        amount = 30.00
        
        result_balance = self.wallet.deduct_funds(amount)
        self.assertEqual(float(self.wallet.balance), initial_balance - amount)
        self.assertEqual(float(result_balance), initial_balance - amount)
    
    def test_deduct_funds_insufficient_balance(self):
        """Test deducting funds with insufficient balance"""
        amount = 150.00  # More than current balance
        
        with self.assertRaises(ValueError):
            self.wallet.deduct_funds(amount)
        self.assertEqual(self.wallet.balance, 100.00)  # Balance unchanged
    
    def test_wallet_str_representation(self):
        """Test wallet string representation"""
        expected = f"{self.user.get_full_name()}'s Wallet - ${self.wallet.balance}"
        self.assertEqual(str(self.wallet), expected)


class FundingRequestModelTest(TestCase):
    """Test cases for FundingRequest model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='1234567893',
            phone_number='09123456792'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('50.00'))
        self.funding_request = FundingRequest.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            description='Test funding request'
        )
    
    def test_funding_request_creation(self):
        """Test creating a funding request"""
        self.assertEqual(self.funding_request.user, self.user)
        self.assertEqual(self.funding_request.amount, Decimal('100.00'))
        self.assertEqual(self.funding_request.status, 'pending')
        self.assertIsNotNone(self.funding_request.requested_at)
    
    def test_funding_request_approval(self):
        """Test approving a funding request"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='1234567894',
            phone_number='09123456793'
        )
        
        initial_balance = self.wallet.balance
        success = self.funding_request.approve(admin_user, 'Approved for testing')
        
        self.assertTrue(success)
        self.assertEqual(self.funding_request.status, 'approved')
        self.assertEqual(self.funding_request.processed_by, admin_user)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance + self.funding_request.amount)
    
    def test_funding_request_rejection(self):
        """Test rejecting a funding request"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_staff=True,
            first_name='Admin',
            last_name='User',
            ssn='1234567894',
            phone_number='09123456793'
        )
        
        success = self.funding_request.reject(admin_user, 'Insufficient documentation')
        
        self.assertTrue(success)
        self.assertEqual(self.funding_request.status, 'rejected')
        self.assertEqual(self.funding_request.processed_by, admin_user)
        # Wallet balance should remain unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 50.00)


class DayOffModelTest(TestCase):
    """Test cases for DayOff model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567895',
            phone_number='09123456794'
        )
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialty='Cardiology',
            fee=100.00
        )
        self.day_off = DayOff.objects.create(
            doctor=self.doctor,
            date=timezone.now().date() + timedelta(days=1),
            reason='Personal appointment'
        )
    
    def test_day_off_creation(self):
        """Test creating a day off"""
        self.assertEqual(self.day_off.doctor, self.doctor)
        self.assertEqual(self.day_off.reason, 'Personal appointment')
        self.assertFalse(self.day_off.is_approved)
    
    def test_day_off_str_representation(self):
        """Test day off string representation"""
        expected = f"{self.doctor.user.get_full_name()} - {self.day_off.date} (Pending)"
        self.assertEqual(str(self.day_off), expected)
    
    def test_day_off_approval(self):
        """Test approving a day off"""
        self.assertFalse(self.day_off.is_approved)
        
        self.day_off.is_approved = True
        self.day_off.save()
        self.assertTrue(self.day_off.is_approved)
    
    def test_day_off_rejection(self):
        """Test rejecting a day off"""
        self.day_off.is_approved = True  # First approve
        self.day_off.save()
        self.day_off.is_approved = False
        self.day_off.save()
        self.assertFalse(self.day_off.is_approved)
