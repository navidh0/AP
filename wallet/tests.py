from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

from .models import Wallet, Transaction, FundingRequest
from doctor.models import Doctor, Timeslot
from booking.models import Appointment

User = get_user_model()


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
            ssn='1234567890',
            phone_number='09123456789'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_wallet_creation(self):
        """Test creating a wallet"""
        self.assertEqual(self.wallet.user, self.user)
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
    
    def test_add_funds(self):
        """Test adding funds to wallet"""
        initial_balance = self.wallet.balance
        amount = 50.00
        
        self.wallet.add_funds(amount)
        self.assertEqual(self.wallet.balance, initial_balance + Decimal(str(amount)))
    
    def test_deduct_funds_sufficient_balance(self):
        """Test deducting funds with sufficient balance"""
        initial_balance = self.wallet.balance
        amount = 30.00
        
        result_balance = self.wallet.deduct_funds(amount)
        self.assertEqual(self.wallet.balance, initial_balance - Decimal(str(amount)))
        self.assertEqual(result_balance, initial_balance - Decimal(str(amount)))
    
    def test_deduct_funds_insufficient_balance(self):
        """Test deducting funds with insufficient balance"""
        amount = 150.00  # More than current balance
        
        with self.assertRaises(ValueError):
            self.wallet.deduct_funds(amount)
        self.assertEqual(self.wallet.balance, Decimal('100.00'))  # Balance unchanged
    
    def test_wallet_str_representation(self):
        """Test wallet string representation"""
        expected = f"{self.user.get_full_name()}'s Wallet - ${self.wallet.balance}"
        self.assertEqual(str(self.wallet), expected)


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='1234567890',
            phone_number='09123456789'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description='Test payment',
            balance_after=Decimal('50.00')
        )
        
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.transaction_type, 'payment')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.balance_after, Decimal('50.00'))
        self.assertIsNotNone(transaction.created_at)
    
    def test_transaction_str_representation(self):
        """Test transaction string representation"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description='Test payment',
            balance_after=Decimal('50.00')
        )
        
        expected = f"{self.user.get_full_name()} - {transaction.transaction_type} - ${transaction.amount}"
        self.assertEqual(str(transaction), expected)


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
            ssn='1234567890',
            phone_number='09123456789'
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
    
    def test_funding_request_str_representation(self):
        """Test funding request string representation"""
        expected = f"{self.user.get_full_name()} - ${self.funding_request.amount} - Pending"
        self.assertEqual(str(self.funding_request), expected)
    
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
            ssn='1234567891',
            phone_number='09123456790'
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
            ssn='1234567891',
            phone_number='09123456790'
        )
        
        success = self.funding_request.reject(admin_user, 'Insufficient documentation')
        
        self.assertTrue(success)
        self.assertEqual(self.funding_request.status, 'rejected')
        self.assertEqual(self.funding_request.processed_by, admin_user)
        # Wallet balance should remain unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50.00'))


class WalletViewsTest(TestCase):
    """Test cases for wallet views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='testpass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            ssn='1234567890',
            phone_number='09123456789'
        )
        self.user.is_active = True
        self.user.save()
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_wallet_detail_view(self):
        """Test wallet detail view"""
        self.client.force_login(self.user)
        url = reverse('wallet:wallet_detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"${self.wallet.balance}")
    
    def test_add_funds_ajax_view(self):
        """Test adding funds via AJAX"""
        self.client.force_login(self.user)
        url = reverse('wallet:add_funds_ajax')
        
        response = self.client.post(url, {
            'amount': 50.00,
            'description': 'Test funding request'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check JSON response
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check if funding request was created
        funding_request = FundingRequest.objects.filter(
            user=self.user,
            amount=50.00
        ).first()
        self.assertIsNotNone(funding_request)
        self.assertEqual(funding_request.status, 'pending')