from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Wallet(models.Model):
    """Model for patient wallet to store balance"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        limit_choices_to={'role': 'patient'}
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Wallet - ${self.balance}"
    
    def add_funds(self, amount):
        """Add funds to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += Decimal(str(amount))
        self.save()
        return self.balance
    
    def deduct_funds(self, amount):
        """Deduct funds from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < Decimal(str(amount)):
            raise ValueError("Insufficient funds")
        self.balance -= Decimal(str(amount))
        self.save()
        return self.balance
    
    def has_sufficient_funds(self, amount):
        """Check if wallet has sufficient funds"""
        return self.balance >= Decimal(str(amount))


class Transaction(models.Model):
    """Model to track wallet transactions"""
    
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    appointment = models.ForeignKey(
        'booking.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.get_full_name()} - {self.transaction_type} - ${self.amount}"