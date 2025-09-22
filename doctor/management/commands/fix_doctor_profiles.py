from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctor.models import Doctor

User = get_user_model()


class Command(BaseCommand):
    help = 'Create missing doctor profiles for existing doctor users'

    def handle(self, *args, **options):
        doctor_users = User.objects.filter(role='doctor')
        self.stdout.write(f"Found {doctor_users.count()} doctor users")
        
        created_count = 0
        for user in doctor_users:
            if not hasattr(user, 'doctor_profile'):
                self.stdout.write(f"Creating doctor profile for {user.username}")
                Doctor.objects.create(
                    user=user,
                    specialty='General Medicine',
                    fee=100.00,
                    verification_status='pending'
                )
                created_count += 1
            else:
                self.stdout.write(f"User {user.username} already has a doctor profile")
        
        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} doctor profiles")
        )
        
        # Check final state
        self.stdout.write(f"Total doctor profiles: {Doctor.objects.count()}")
        pending_doctors = Doctor.objects.filter(verification_status='pending')
        self.stdout.write(f"Pending verification: {pending_doctors.count()}")
