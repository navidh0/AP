from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """Model for user notifications"""
    
    NOTIFICATION_TYPES = [
        ('appointment_booked', 'Appointment Booked'),
        ('appointment_confirmed', 'Appointment Confirmed'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('appointment_cancelled_by_doctor', 'Appointment Cancelled by Doctor'),
        ('refund_processed', 'Refund Processed'),
        ('wallet_funded', 'Wallet Funded'),
        ('wallet_funding_approved', 'Wallet Funding Approved'),
        ('wallet_funding_rejected', 'Wallet Funding Rejected'),
        ('day_off_approved', 'Day Off Approved'),
        ('day_off_rejected', 'Day Off Rejected'),
        ('profile_change_approved', 'Profile Change Approved'),
        ('profile_change_rejected', 'Profile Change Rejected'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional foreign keys for related objects
    appointment = models.ForeignKey(
        'booking.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, appointment=None):
        """Create a new notification"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            appointment=appointment
        )
