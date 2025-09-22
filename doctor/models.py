from django.db import models
from django.utils import timezone
from django.conf import settings
from users.models import User
from django.db.models import Q


# -----------------------------
# Doctor QuerySet & Manager
# -----------------------------
class DoctorQuerySet(models.QuerySet):
    def available(self):
        """Return doctors who are marked as available."""
        return self.filter(availability=True)

    def search(self, name=None, specialty=None):
        """Search doctors by name, specialty, or both."""
        from django.db.models import Q
        qs = self
        if name:
            qs = qs.filter(
                Q(user__username__icontains=name)
                | Q(user__first_name__icontains=name)
                | Q(user__last_name__icontains=name)
                | Q(user__email__icontains=name)
            )
        if specialty:
            qs = qs.filter(specialty__icontains=specialty)
        return qs


class DoctorManager(models.Manager):
    def get_queryset(self):
        return DoctorQuerySet(self.model, using=self._db)

    def available(self):
        return self.get_queryset().available()

    def search(self, name=None, specialty=None):
        return self.get_queryset().search(name=name, specialty=specialty)


# -----------------------------
# Doctor Model
# -----------------------------
class Doctor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        limit_choices_to={"role": "doctor"},  # only link Users with role=doctor
    )
    specialty = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Doctor's average rating from reviews")
    availability = models.BooleanField(default=True)  # can this doctor take appointments?
    average_rating = models.FloatField(default=0.0)
    
    # Verification fields
    is_verified = models.BooleanField(default=False, help_text="Whether the doctor's credentials have been verified")
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        default='pending'
    )
    verification_notes = models.TextField(blank=True, null=True, help_text="Admin notes about verification")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_doctors',
        limit_choices_to={'is_staff': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DoctorManager()

    class Meta:
        ordering = ["specialty", "user__username"]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialty}"
    
    def verify(self, admin_user, notes=None):
        """Verify the doctor (can be used for initial verification or re-verification)"""
        if self.verification_status not in ['pending', 'rejected']:
            return False
        
        self.is_verified = True
        self.verification_status = 'verified'
        self.verified_at = timezone.now()
        self.verified_by = admin_user
        if notes:
            self.verification_notes = notes
        self.save()
        return True
    
    def reject_verification(self, admin_user, notes=None):
        """Reject doctor verification"""
        if self.verification_status not in ['pending', 'verified']:
            return False
        
        self.is_verified = False
        self.verification_status = 'rejected'
        self.verified_at = timezone.now()
        self.verified_by = admin_user
        if notes:
            self.verification_notes = notes
        self.save()
        return True
    
    def suspend(self, admin_user, notes=None):
        """Suspend the doctor"""
        self.is_verified = False
        self.verification_status = 'suspended'
        self.verified_at = timezone.now()
        self.verified_by = admin_user
        if notes:
            self.verification_notes = notes
        self.save()
        return True
    
    def toggle_availability(self):
        """Toggle doctor availability"""
        self.availability = not self.availability
        self.save()
        return self.availability
    
    def calculate_average_rating(self):
        """Calculate average rating from comments"""
        from django.db.models import Avg
        avg_rating = self.comments.aggregate(avg_rating=Avg('doctor_rating'))['avg_rating']
        if avg_rating is not None:
            self.rating = round(avg_rating, 2)
            self.average_rating = float(avg_rating)
        else:
            self.rating = 0.0
            self.average_rating = 0.0
        self.save()
        return self.rating


# -----------------------------
# Day Off Model
# -----------------------------
class DayOff(models.Model):
    """Model for doctor's days off"""
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="days_off"
    )
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ('doctor', 'date')
    
    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.date} ({'Approved' if self.is_approved else 'Pending'})"
    
    def delete_timeslots_for_date(self):
        """Delete all timeslots for this day off date and handle existing appointments"""
        from .models import Timeslot
        from booking.models import Appointment
        from wallet.models import Wallet, Transaction
        from django.db import transaction
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get all timeslots for this date
        timeslots = Timeslot.objects.filter(
            doctor=self.doctor,
            start_time__date=self.date
        )
        
        refunded_appointments = []
        
        with transaction.atomic():
            for timeslot in timeslots:
                # Check if there's an appointment for this timeslot
                try:
                    appointment = Appointment.objects.get(timeslot=timeslot)
                    
                    # Only refund if appointment is not already cancelled or completed
                    if appointment.status in ['scheduled', 'confirmed']:
                        # Get patient's wallet
                        wallet, created = Wallet.objects.get_or_create(user=appointment.patient)
                        
                        # Refund the doctor's fee
                        refund_amount = self.doctor.fee
                        wallet.add_funds(refund_amount)
                        
                        # Create refund transaction
                        Transaction.objects.create(
                            wallet=wallet,
                            transaction_type='refund',
                            amount=refund_amount,
                            description=f'Refund for cancelled appointment due to doctor day off on {self.date}',
                            balance_after=wallet.balance,
                            appointment=appointment
                        )
                        
                        # Cancel the appointment
                        appointment.status = 'cancelled'
                        appointment.save()
                        
                        # Create notification for the patient
                        from core.models import Notification
                        notification = Notification.create_notification(
                            user=appointment.patient,
                            notification_type='appointment_cancelled_by_doctor',
                            title='Appointment Cancelled - Doctor Day Off',
                            message=f'Your appointment with Dr. {self.doctor.user.get_full_name()} on {self.date} has been cancelled due to a doctor day off. A refund of ${refund_amount} has been processed to your wallet.',
                            appointment=appointment
                        )
                        
                        # Create separate notification for refund
                        Notification.create_notification(
                            user=appointment.patient,
                            notification_type='refund_processed',
                            title='Refund Processed - Doctor Day Off',
                            message=f'Refund of ${refund_amount} has been added to your wallet for the cancelled appointment due to doctor day off.',
                            appointment=appointment
                        )
                        
                        refunded_appointments.append({
                            'patient': appointment.patient,
                            'appointment': appointment,
                            'refund_amount': refund_amount
                        })
                        
                except Appointment.DoesNotExist:
                    # No appointment for this timeslot, just delete it
                    pass
            
            # Delete all timeslots for this date
            deleted_count = timeslots.delete()[0]
        
        return deleted_count, refunded_appointments


# -----------------------------
# Profile Change Request Model
# -----------------------------
class ProfileChangeRequest(models.Model):
    """Model for doctor profile changes that require admin approval"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="profile_change_requests"
    )
    field_name = models.CharField(max_length=100, help_text="Name of the field being changed")
    old_value = models.TextField(help_text="Current value")
    new_value = models.TextField(help_text="Requested new value")
    reason = models.TextField(help_text="Reason for the change")
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
        related_name='processed_profile_changes',
        limit_choices_to={'is_staff': True}
    )
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.field_name} change ({self.get_status_display()})"
    
    def approve(self, admin_user, notes=None):
        """Approve the profile change request"""
        if self.status != 'pending':
            return False
        
        try:
            # Apply the change to the doctor profile
            setattr(self.doctor, self.field_name, self.new_value)
            self.doctor.save()
            
            # Update request status
            self.status = 'approved'
            self.processed_at = timezone.now()
            self.processed_by = admin_user
            if notes:
                self.admin_notes = notes
            self.save()
            
            return True
        except Exception as e:
            return False
    
    def reject(self, admin_user, notes=None):
        """Reject the profile change request"""
        if self.status != 'pending':
            return False
        
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.processed_by = admin_user
        if notes:
            self.admin_notes = notes
        self.save()
        
        return True


# -----------------------------
# Doctor Availability Model
# -----------------------------
class DoctorAvailability(models.Model):
    """Model for doctor's availability windows"""
    
    DAYS_OF_WEEK = [
        (0, 'Saturday'),
        (1, 'Sunday'),
        (2, 'Monday'),
        (3, 'Tuesday'),
        (4, 'Wednesday'),
        (5, 'Thursday'),
        (6, 'Friday'),
    ]
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    visit_duration = models.PositiveIntegerField(
        default=30,
        help_text="Duration of each visit in minutes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ('doctor', 'day_of_week', 'start_time', 'end_time')
    
    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def get_iranian_weekday(self, target_date):
        """Convert Python weekday to Iranian calendar weekday"""
        # Python weekday: Monday=0, Tuesday=1, ..., Sunday=6
        # Iranian weekday: Saturday=0, Sunday=1, ..., Friday=6
        python_weekday = target_date.weekday()
        iranian_weekday = (python_weekday + 2) % 7  # Convert to Iranian format
        return iranian_weekday
    
    def generate_timeslots_for_date(self, target_date):
        """Generate timeslots for a specific date based on this availability"""
        from datetime import datetime, timedelta
        
        # Check if the target date matches this day of week (Iranian format)
        if self.get_iranian_weekday(target_date) != self.day_of_week:
            return []
        
        # Create datetime objects for start and end times
        start_datetime = datetime.combine(target_date, self.start_time)
        end_datetime = datetime.combine(target_date, self.end_time)
        
        # Generate timeslots
        timeslots = []
        current_time = start_datetime
        
        while current_time + timedelta(minutes=self.visit_duration) <= end_datetime:
            end_time = current_time + timedelta(minutes=self.visit_duration)
            
            # Check if timeslot already exists
            if not Timeslot.objects.filter(
                doctor=self.doctor,
                start_time=current_time,
                end_time=end_time
            ).exists():
                timeslot = Timeslot.objects.create(
                    doctor=self.doctor,
                    start_time=current_time,
                    end_time=end_time,
                    is_booked=False,
                    created_from_availability=self
                )
                timeslots.append(timeslot)
            
            current_time += timedelta(minutes=self.visit_duration)
        
        return timeslots


# -----------------------------
# Timeslot Model
# -----------------------------
class Timeslot(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="timeslots"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    created_from_availability = models.ForeignKey(
        DoctorAvailability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_timeslots"
    )

    class Meta:
        ordering = ["start_time"]
        unique_together = ("doctor", "start_time", "end_time")

    def __str__(self):
        status = "Booked" if self.is_booked else "Available"
        return f"{self.doctor} | {self.start_time:%Y-%m-%d %H:%M} - {status}"

    def book(self):
        """Mark timeslot as booked."""
        if not self.is_booked:
            self.is_booked = True
            self.save()
            return True
        return False

    def cancel(self):
        """Cancel (free up) a booked timeslot."""
        if self.is_booked:
            self.is_booked = False
            self.save()
            return True
        return False

    def is_future(self):
        """Check if this timeslot is still in the future."""
        return self.start_time > timezone.now()
    
    @classmethod
    def generate_for_doctor(cls, doctor, start_date, end_date):
        """Generate timeslots for a doctor within a date range"""
        from datetime import timedelta
        
        generated_timeslots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get all active availabilities for this doctor
            availabilities = DoctorAvailability.objects.filter(
                doctor=doctor,
                is_active=True
            )
            
            for availability in availabilities:
                timeslots = availability.generate_timeslots_for_date(current_date)
                generated_timeslots.extend(timeslots)
            
            current_date += timedelta(days=1)
        
        return generated_timeslots





#+++++++++++++++++++++++++++Comment--------------------



# -----------------------------
# Comment QuerySet & Manager
# -----------------------------
class CommentQuerySet(models.QuerySet): #return rows of data from specifc models
    def get_for_doctor(self, doctor):
        """ return comments for specific doctor """
        return self.filter(doctor=doctor)

    def by_rating(self, min_rating=None, max_rating=None):
        """ filter the doctor by rating """
        qs = self
        if min_rating:
            qs = qs.filter(doctor_rating__gte=min_rating)
        if max_rating:
            qs = qs.filter(doctor_rating__lte=max_rating)
        return qs

    def recent(self, days=30):
        """ Return the comment for specific last days """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)    




class CommentManager(models.Manager): #handle the relation between model and database 
    def get_queryset(self):
        return CommentQuerySet(self.model, using=self._db)

    def get_for_doctor(self, doctor):
        return  self.get_queryset().get_for_doctor(doctor)

    def by_rating(self, min_rating=None, max_rating=None):
        return self.get_queryset().by_rating(min_rating, max_rating)

    def recent(self, days=30):
        return self.get_queryset().recent(days)




# -----------------------------
# Comment models
# -----------------------------
class Comment(models.Model):
    #This static data about doctor likert scale 
    #DOCTOR_LIKERT_RATE = [(i, str(i)) for i in range(1, 6)]
    DOCTOR_LIKERT_RATE = [
        (1, "Very Poor"),
        (2, "Poor"),
        (3, "Average"),
        (4, "Good"),
        (5, "Excellent"),
    ]



    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='comments')

    user = models.ForeignKey(User,
        on_delete=models.CASCADE,
        related_name='doctor_comment',
        limit_choices_to={'role': 'patient'}
      )

    title = models.CharField(max_length=200, help_text="Brief title for comment")
    description = models.TextField(help_text="Detail review of the doctor ")
    doctor_rating = models.IntegerField(choices=DOCTOR_LIKERT_RATE,
        default=1,
        help_text="Rate the doctor from 1(Very bad ) to 5(Excellent)"
        )

    objects = CommentManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_anonymous = models.BooleanField(
        default=False,
        help_text="Hide user identity in public display "
    )


    def __str__(self):
        return f"{self.user.username}'s review of Dr. {self.doctor.user.get_full_name() or self.doctor.user.username}"
    
    def get_display_name(self):
        """ Get display name based on anonimity setting """
        if self.is_anonymous:
            return "Anonymous Patient"
        return self.user.get_full_name() or self.user.username 
    
    def get_display_rating(self):
         return dict(self.DOCTOR_LIKERT_RATE)[self.doctor_rating]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update doctor's average rating when comment is saved
        self.doctor.calculate_average_rating()
    
    def delete(self, *args, **kwargs):
        doctor = self.doctor
        super().delete(*args, **kwargs)
        # Update doctor's average rating when comment is deleted
        doctor.calculate_average_rating()

