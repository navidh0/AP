from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Appointment
from doctor.models import Doctor, Timeslot, DoctorAvailability
from wallet.models import Wallet, Transaction
from core.models import Notification

User = get_user_model()


class AppointmentModelTest(TestCase):
    """Test cases for Appointment model"""
    
    def setUp(self):
        # Create users
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='testpass123',
            role='doctor',
            first_name='Dr. John',
            last_name='Doe',
            ssn='0000000010',
            phone_number='09100000000'
        )
        self.doctor_user.is_active = True
        self.doctor_user.save()
        
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='0000000011',
            phone_number='09200000000'
        )
        self.patient_user.is_active = True
        self.patient_user.save()
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=100.00
        )
        
        # Create timeslot
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(minutes=30)
        self.timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create wallet for patient
        self.wallet = Wallet.objects.create(user=self.patient_user, balance=200.00)
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            timeslot=self.timeslot,
            status='scheduled'
        )
    
    def test_appointment_creation(self):
        """Test creating an appointment"""
        self.assertEqual(self.appointment.patient, self.patient_user)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.timeslot, self.timeslot)
        self.assertEqual(self.appointment.status, 'scheduled')
        self.assertIsNotNone(self.appointment.created_at)
    
    def test_appointment_str_representation(self):
        """Test appointment string representation"""
        expected = f"{self.patient_user.get_full_name()} - {self.doctor} - {self.appointment.timeslot.start_time}"
        self.assertEqual(str(self.appointment), expected)
    
    def test_appointment_cannot_be_cancelled_within_24_hours(self):
        """Test that appointment cannot be cancelled within 24 hours"""
        # Create appointment for tomorrow (within 24 hours)
        future_time = timezone.now() + timedelta(hours=12)
        future_timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=future_time,
            end_time=future_time + timedelta(minutes=30)
        )
        future_appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            timeslot=future_timeslot,
            status='scheduled'
        )
        
        self.assertFalse(future_appointment.can_be_cancelled())
    
    def test_appointment_can_be_cancelled_after_24_hours(self):
        """Test that appointment can be cancelled after 24 hours"""
        # Create appointment for 2 days from now (more than 24 hours)
        future_time = timezone.now() + timedelta(days=2)
        future_timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=future_time,
            end_time=future_time + timedelta(minutes=30)
        )
        future_appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor,
            timeslot=future_timeslot,
            status='scheduled'
        )
        
        self.assertTrue(future_appointment.can_be_cancelled())