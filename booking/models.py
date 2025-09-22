from django.db import models
from django.utils import timezone
from django.conf import settings
from doctor.models import Doctor, Timeslot


class Appointment(models.Model):
    """Model for patient appointments with doctors"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    timeslot = models.OneToOneField(
        Timeslot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['timeslot__start_time']
        unique_together = ['patient', 'timeslot']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.doctor} - {self.timeslot.start_time}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically book the timeslot"""
        if not self.pk:  # New appointment
            if self.timeslot.is_booked:
                raise ValueError("This timeslot is already booked")
            self.timeslot.book()
        super().save(*args, **kwargs)
    
    def cancel(self):
        """Cancel the appointment and free up the timeslot"""
        if self.status not in ['cancelled', 'completed']:
            self.status = 'cancelled'
            self.timeslot.cancel()
            self.save()
            return True
        return False
    
    def is_future(self):
        """Check if appointment is in the future"""
        return self.timeslot.start_time > timezone.now()
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled (more than 24 hours away)"""
        if self.status in ['cancelled', 'completed']:
            return False
        
        # Check if appointment is more than 24 hours away
        time_until_appointment = self.timeslot.start_time - timezone.now()
        return time_until_appointment.total_seconds() > 24 * 3600  # 24 hours in seconds