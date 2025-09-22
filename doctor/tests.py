from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from .models import Doctor, Timeslot, DoctorAvailability, DayOff, Comment
from booking.models import Appointment
from wallet.models import Wallet

User = get_user_model()


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
            ssn='1234567890',
            phone_number='09123456789'
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
            ssn='1234567893',
            phone_number='09123456792'
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
            ssn='1234567894',
            phone_number='09123456793'
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
            ssn='1234567895',
            phone_number='09123456794'
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
    
    def test_calculate_average_rating(self):
        """Test calculating average rating from comments"""
        # Create a patient user
        patient_user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient'
        )
        
        # Create comments with different ratings
        Comment.objects.create(
            doctor=self.doctor,
            user=patient_user,
            doctor_rating=5,
            title='Excellent',
            description='Excellent doctor!'
        )
        Comment.objects.create(
            doctor=self.doctor,
            user=patient_user,
            doctor_rating=4,
            title='Very Good',
            description='Very good doctor!'
        )
        
        # Calculate average rating
        self.doctor.calculate_average_rating()
        
        self.assertEqual(self.doctor.rating, 4.5)  # (5 + 4) / 2


class TimeslotModelTest(TestCase):
    """Test cases for Timeslot model"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567892',
            phone_number='09123456791'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(minutes=30)
        self.timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=start_time,
            end_time=end_time
        )
    
    def test_timeslot_creation(self):
        """Test creating a timeslot"""
        self.assertEqual(self.timeslot.doctor, self.doctor)
        self.assertFalse(self.timeslot.is_booked)
        self.assertIsNotNone(self.timeslot.start_time)
        self.assertIsNotNone(self.timeslot.end_time)
    
    def test_timeslot_str_representation(self):
        """Test timeslot string representation"""
        expected = f"{self.doctor} | {self.timeslot.start_time.strftime('%Y-%m-%d %H:%M')} - Available"
        self.assertEqual(str(self.timeslot), expected)
    
    def test_timeslot_is_available(self):
        """Test timeslot availability check"""
        # Timeslot should be available initially (not booked)
        self.assertFalse(self.timeslot.is_booked)
        
        # Mark as booked
        self.timeslot.is_booked = True
        self.timeslot.save()
        
        # Should be booked now
        self.assertTrue(self.timeslot.is_booked)


class DoctorAvailabilityModelTest(TestCase):
    """Test cases for DoctorAvailability model"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567892',
            phone_number='09123456791'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        self.availability = DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=1,  # Monday
            start_time='09:00:00',
            end_time='17:00:00',
            visit_duration=30,
            is_active=True
        )
    
    def test_availability_creation(self):
        """Test creating doctor availability"""
        self.assertEqual(self.availability.doctor, self.doctor)
        self.assertEqual(self.availability.day_of_week, 1)
        self.assertEqual(self.availability.start_time, '09:00:00')
        self.assertEqual(self.availability.end_time, '17:00:00')
        self.assertEqual(self.availability.visit_duration, 30)
        self.assertTrue(self.availability.is_active)
    
    def test_availability_str_representation(self):
        """Test availability string representation"""
        expected = f"{self.doctor} - Sunday 09:00:00-17:00:00"
        self.assertEqual(str(self.availability), expected)


class DayOffModelTest(TestCase):
    """Test cases for DayOff model"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567892',
            phone_number='09123456791'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
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


class CommentModelTest(TestCase):
    """Test cases for Comment model"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            ssn='1234567892',
            phone_number='09123456791'
        )
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='1234567891',
            phone_number='09123456790'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        self.comment = Comment.objects.create(
            doctor=self.doctor,
            user=self.patient_user,
            doctor_rating=5,
            title='Great Doctor',
            description='Excellent doctor!'
        )
    
    def test_comment_creation(self):
        """Test creating a comment"""
        self.assertEqual(self.comment.doctor, self.doctor)
        self.assertEqual(self.comment.user, self.patient_user)
        self.assertEqual(self.comment.doctor_rating, 5)
        self.assertEqual(self.comment.description, 'Excellent doctor!')
    
    def test_comment_str_representation(self):
        """Test comment string representation"""
        expected = f"{self.patient_user.username}'s review of Dr. {self.doctor.user.get_full_name()}"
        self.assertEqual(str(self.comment), expected)
    
    def test_comment_auto_updates_doctor_rating(self):
        """Test that comment creation updates doctor rating"""
        # Create another comment
        Comment.objects.create(
            doctor=self.doctor,
            user=self.patient_user,
            doctor_rating=4,
            title='Very Good',
            description='Very good doctor!'
        )
        
        # Check if doctor rating was updated
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.rating, 4.5)  # (5 + 4) / 2