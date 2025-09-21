from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from users.models import User
# -----------------------------
# Doctor QuerySet & Manager
# -----------------------------
class DoctorQuerySet(models.QuerySet):
    def available(self):
        """Return doctors who are marked as available."""
        return self.filter(availability=True)

    def search(self, name=None, specialty=None):
        """Search doctors by name, specialty, or both."""
        qs = self
        if name:
            qs = qs.filter(
                Q(user__username__icontains=name)
                | Q(user__first_name__icontains=name)
                | Q(user__last_name__icontains=name)
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        limit_choices_to={"role": "doctor"},  # only link Users with role=doctor
    )
    specialty = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.BooleanField(default=True)  # can this doctor take appointments?
    average_rating = models.FloatField(default=0.0)

    objects = DoctorManager()

    class Meta:
        ordering = ["specialty", "user__username"]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialty}"


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

