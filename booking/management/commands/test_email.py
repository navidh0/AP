from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User
from doctor.models import Doctor, Timeslot
from booking.models import Appointment
from booking.services import send_appointment_confirmation_email


class Command(BaseCommand):
    help = 'Test email functionality by creating a sample appointment and sending confirmation email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            required=True
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Testing email functionality for: {email}')
        
        try:
            # Get or create a test patient user
            import random
            random_suffix = random.randint(1000, 9999)
            patient, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': f"{email.split('@')[0]}_{random_suffix}",
                    'first_name': 'Test',
                    'last_name': 'Patient',
                    'role': 'patient',
                    'phone_number': f'0912345{random_suffix}',
                    'ssn': f'{random_suffix}{random.randint(100000, 999999)}',
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created test patient: {patient.email}'))
            else:
                self.stdout.write(f'Using existing patient: {patient.email}')
            
            # Get or create a test doctor
            doctor_user, created = User.objects.get_or_create(
                username='testdoctor',
                defaults={
                    'email': 'testdoctor@example.com',
                    'first_name': 'Test',
                    'last_name': 'Doctor',
                    'role': 'doctor',
                    'phone_number': '09987654321',
                    'ssn': '0987654321',
                }
            )
            
            doctor, created = Doctor.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'specialty': 'General Practice',
                    'fee': 100.00,
                    'availability': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created test doctor: {doctor}'))
            else:
                self.stdout.write(f'Using existing doctor: {doctor}')
            
            # Create a test timeslot
            start_time = timezone.now() + timedelta(days=1, hours=10)
            end_time = start_time + timedelta(hours=1)
            
            timeslot, created = Timeslot.objects.get_or_create(
                doctor=doctor,
                start_time=start_time,
                end_time=end_time,
                defaults={'is_booked': False}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created test timeslot: {timeslot}'))
            else:
                self.stdout.write(f'Using existing timeslot: {timeslot}')
            
            # Create a test appointment
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                timeslot=timeslot,
                defaults={
                    'status': 'scheduled',
                    'notes': 'This is a test appointment for email functionality testing.',
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created test appointment: {appointment}'))
            else:
                self.stdout.write(f'Using existing appointment: {appointment}')
            
            # Send test email
            self.stdout.write('Sending test email...')
            success = send_appointment_confirmation_email(appointment)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Test email sent successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to send test email.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during email test: {str(e)}')
            )
