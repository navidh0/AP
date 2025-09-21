from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Wallet, Transaction
from booking.models import Appointment
from doctor.models import Doctor, Timeslot
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class WalletModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.patient = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role='patient',
            phone_number='09123456789',
            ssn='1234567890'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            role='doctor',
            phone_number='09123456788',
            ssn='1234567891'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=Decimal('100.00'),
            availability=True
        )
        
        # Create a future timeslot
        future_time = timezone.now() + timedelta(days=1)
        self.timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=future_time,
            end_time=future_time + timedelta(hours=1),
            is_booked=False
        )
        
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            timeslot=self.timeslot,
            status='scheduled'
        )

    def test_wallet_creation(self):
        """Test wallet creation for patient"""
        wallet = Wallet.objects.create(user=self.patient)
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertEqual(wallet.user, self.patient)

    def test_add_funds(self):
        """Test adding funds to wallet"""
        wallet = Wallet.objects.create(user=self.patient)
        new_balance = wallet.add_funds(Decimal('50.00'))
        self.assertEqual(new_balance, Decimal('50.00'))
        self.assertEqual(wallet.balance, Decimal('50.00'))

    def test_deduct_funds_sufficient(self):
        """Test deducting funds when sufficient balance"""
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('100.00'))
        new_balance = wallet.deduct_funds(Decimal('30.00'))
        self.assertEqual(new_balance, Decimal('70.00'))
        self.assertEqual(wallet.balance, Decimal('70.00'))

    def test_deduct_funds_insufficient(self):
        """Test deducting funds when insufficient balance"""
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('20.00'))
        with self.assertRaises(ValueError):
            wallet.deduct_funds(Decimal('30.00'))

    def test_has_sufficient_funds(self):
        """Test checking sufficient funds"""
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('50.00'))
        self.assertTrue(wallet.has_sufficient_funds(Decimal('30.00')))
        self.assertFalse(wallet.has_sufficient_funds(Decimal('60.00')))

    def test_transaction_creation(self):
        """Test transaction creation"""
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('100.00'))
        transaction = Transaction.objects.create(
            wallet=wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description='Test payment',
            balance_after=Decimal('50.00'),
            appointment=self.appointment
        )
        self.assertEqual(transaction.wallet, wallet)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.appointment, self.appointment)

    def test_negative_amount_validation(self):
        """Test that negative amounts are rejected"""
        wallet = Wallet.objects.create(user=self.patient)
        with self.assertRaises(ValueError):
            wallet.add_funds(Decimal('-10.00'))
        
        with self.assertRaises(ValueError):
            wallet.deduct_funds(Decimal('-10.00'))


class WalletPaymentIntegrationTest(TestCase):
    def setUp(self):
        """Set up test data for payment integration"""
        self.patient = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role='patient',
            phone_number='09123456789',
            ssn='1234567890'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            role='doctor',
            phone_number='09123456788',
            ssn='1234567891'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            fee=Decimal('100.00'),
            availability=True
        )
        
        # Create a future timeslot
        future_time = timezone.now() + timedelta(days=1)
        self.timeslot = Timeslot.objects.create(
            doctor=self.doctor,
            start_time=future_time,
            end_time=future_time + timedelta(hours=1),
            is_booked=False
        )
        
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            timeslot=self.timeslot,
            status='scheduled'
        )

    def test_successful_payment_flow(self):
        """Test complete payment flow"""
        # Create wallet with sufficient funds
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('150.00'))
        
        # Process payment
        new_balance = wallet.deduct_funds(self.doctor.fee)
        
        # Create transaction record
        transaction = Transaction.objects.create(
            wallet=wallet,
            transaction_type='payment',
            amount=self.doctor.fee,
            description=f'Payment for appointment with Dr. {self.doctor.user.get_full_name()}',
            balance_after=new_balance,
            appointment=self.appointment
        )
        
        # Update appointment status
        self.appointment.status = 'confirmed'
        self.appointment.save()
        
        # Verify results
        self.assertEqual(wallet.balance, Decimal('50.00'))
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(self.appointment.status, 'confirmed')

    def test_insufficient_funds_payment(self):
        """Test payment with insufficient funds"""
        # Create wallet with insufficient funds
        wallet = Wallet.objects.create(user=self.patient, balance=Decimal('50.00'))
        
        # Attempt payment should fail
        with self.assertRaises(ValueError):
            wallet.deduct_funds(self.doctor.fee)
        
        # Verify appointment status unchanged
        self.assertEqual(self.appointment.status, 'scheduled')