from django.db import models
from django.utils import timezone
from django.conf import settings
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
