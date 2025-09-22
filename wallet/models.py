from django.db import models, transaction
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
        self.balance = self.balance + Decimal(str(amount))
        self.save()
        return self.balance
    
    def deduct_funds(self, amount):
        """Deduct funds from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < Decimal(str(amount)):
            raise ValueError("Insufficient funds")
        self.balance = self.balance - Decimal(str(amount))
        self.save()
        return self.balance
    
    def has_sufficient_funds(self, amount):
        """Check if wallet has sufficient funds"""
        return self.balance >= Decimal(str(amount))


class FundingRequest(models.Model):
    """Model for funding requests that require admin approval"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='funding_requests',
        limit_choices_to={'role': 'patient'}
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, default='Funds addition request')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_notes = models.TextField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_funding_requests',
        limit_choices_to={'is_staff': True}
    )
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - ${self.amount} - {self.get_status_display()}"
    
    def approve(self, admin_user, notes=None):
        """Approve the funding request"""
        if self.status != 'pending':
            return False
        
        try:
            with transaction.atomic():
                # Get or create wallet
                wallet, created = Wallet.objects.get_or_create(user=self.user)
                
                # Add funds to wallet
                new_balance = wallet.add_funds(self.amount)
                
                # Create transaction record
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=self.amount,
                    description=f'Approved funding request: {self.description}',
                    balance_after=new_balance
                )
                
                # Update request status
                self.status = 'approved'
                self.processed_at = timezone.now()
                self.processed_by = admin_user
                if notes:
                    self.admin_notes = notes
                self.save()
                
                # Create notification for approved funding
                from core.models import Notification
                Notification.create_notification(
                    user=self.user,
                    notification_type='wallet_funding_approved',
                    title='Funding Request Approved',
                    message=f'Your funding request for ${self.amount} has been approved and added to your wallet. New balance: ${new_balance}',
                    appointment=None
                )
                
                return True
        except Exception as e:
            return False
    
    def reject(self, admin_user, notes=None):
        """Reject the funding request"""
        if self.status != 'pending':
            return False
        
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.processed_by = admin_user
        if notes:
            self.admin_notes = notes
        self.save()
        
        # Create notification for rejected funding
        from core.models import Notification
        Notification.create_notification(
            user=self.user,
            notification_type='wallet_funding_rejected',
            title='Funding Request Rejected',
            message=f'Your funding request for ${self.amount} has been rejected. Reason: {notes if notes else "No reason provided"}',
            appointment=None
        )
        
        return True


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
    funding_request = models.ForeignKey(
        FundingRequest,
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