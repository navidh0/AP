from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Doctor

User = get_user_model()


@receiver(post_save, sender=User)
def create_doctor_profile(sender, instance, created, **kwargs):
    """
    Automatically create a doctor profile when a user with role 'doctor' is created.
    """
    if created and instance.role == 'doctor':
        Doctor.objects.create(
            user=instance,
            specialty='General Medicine',  # Default specialty
            fee=100.00,  # Default fee
            verification_status='pending'  # Start as pending verification
        )


@receiver(post_save, sender=User)
def save_doctor_profile(sender, instance, **kwargs):
    """
    Save the doctor profile when the user is saved.
    """
    if hasattr(instance, 'doctor_profile') and instance.role == 'doctor':
        instance.doctor_profile.save()
