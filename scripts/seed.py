#!/usr/bin/env python
"""
Database seeding script for MediCare Django project.
This script populates the database with sample data for testing.
"""

import os
import sys
import django
from datetime import datetime, timedelta, date, time
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from doctor.models import Doctor, DoctorAvailability, Timeslot, Comment
from booking.models import Appointment
from wallet.models import Wallet, Transaction

User = get_user_model()


def create_users():
    """Create sample users (admin, doctors, patients)"""
    
    users_data = [
        # Admin user
        {
            'username': 'admin',
            'email': 'admin@medicare.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'phone_number': '+989123456789',
            'ssn': '1234567890',
            'role': 'admin',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        # Doctor users
        {
            'username': 'dr_smith',
            'email': 'dr.smith@medicare.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone_number': '+989123456790',
            'ssn': '1234567891',
            'role': 'doctor',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        {
            'username': 'dr_johnson',
            'email': 'dr.johnson@medicare.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'phone_number': '+989123456791',
            'ssn': '1234567892',
            'role': 'doctor',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        {
            'username': 'dr_williams',
            'email': 'dr.williams@medicare.com',
            'first_name': 'Michael',
            'last_name': 'Williams',
            'phone_number': '+989123456792',
            'ssn': '1234567893',
            'role': 'doctor',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        # Patient users
        {
            'username': 'patient1',
            'email': 'patient1@example.com',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'phone_number': '+989123456793',
            'ssn': '1234567894',
            'role': 'patient',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        {
            'username': 'patient2',
            'email': 'patient2@example.com',
            'first_name': 'Bob',
            'last_name': 'Davis',
            'phone_number': '+989123456794',
            'ssn': '1234567895',
            'role': 'patient',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
        {
            'username': 'patient3',
            'email': 'patient3@example.com',
            'first_name': 'Carol',
            'last_name': 'Wilson',
            'phone_number': '+989123456795',
            'ssn': '1234567896',
            'role': 'patient',
            'is_active': True,
            'is_email_verified': True,
            'is_phone_verified': True,
        },
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        if created:
            user.set_password('password123')  # Default password for all users
            user.save()
            created_users.append(user)
        else:
            created_users.append(user)
    
    return created_users


def create_doctors(users):
    """Create doctor profiles"""
    
    doctors_data = [
        {
            'user': next(u for u in users if u.username == 'dr_smith'),
            'specialty': 'Cardiology',
            'fee': Decimal('150.00'),
            'availability': True,
            'average_rating': 4.8,
        },
        {
            'user': next(u for u in users if u.username == 'dr_johnson'),
            'specialty': 'Dermatology',
            'fee': Decimal('120.00'),
            'availability': True,
            'average_rating': 4.6,
        },
        {
            'user': next(u for u in users if u.username == 'dr_williams'),
            'specialty': 'Pediatrics',
            'fee': Decimal('100.00'),
            'availability': True,
            'average_rating': 4.9,
        },
    ]
    
    created_doctors = []
    for doctor_data in doctors_data:
        doctor, created = Doctor.objects.get_or_create(
            user=doctor_data['user'],
            defaults=doctor_data
        )
        if created:
            created_doctors.append(doctor)
        else:
            created_doctors.append(doctor)
    
    return created_doctors


def create_doctor_availabilities(doctors):
    """Create availability windows for doctors"""
    
    # Common availability patterns
    availability_patterns = [
        # Monday to Friday, 9 AM to 5 PM, 30-minute slots
        {'day_of_week': 0, 'start_time': time(9, 0), 'end_time': time(17, 0), 'visit_duration': 30},
        {'day_of_week': 1, 'start_time': time(9, 0), 'end_time': time(17, 0), 'visit_duration': 30},
        {'day_of_week': 2, 'start_time': time(9, 0), 'end_time': time(17, 0), 'visit_duration': 30},
        {'day_of_week': 3, 'start_time': time(9, 0), 'end_time': time(17, 0), 'visit_duration': 30},
        {'day_of_week': 4, 'start_time': time(9, 0), 'end_time': time(17, 0), 'visit_duration': 30},
        # Saturday, 10 AM to 2 PM, 45-minute slots
        {'day_of_week': 5, 'start_time': time(10, 0), 'end_time': time(14, 0), 'visit_duration': 45},
    ]
    
    created_availabilities = []
    for doctor in doctors:
        for pattern in availability_patterns:
            availability, created = DoctorAvailability.objects.get_or_create(
                doctor=doctor,
                day_of_week=pattern['day_of_week'],
                start_time=pattern['start_time'],
                end_time=pattern['end_time'],
                defaults={
                    'visit_duration': pattern['visit_duration'],
                    'is_active': True,
                }
            )
            if created:
                created_availabilities.append(availability)
    
    return created_availabilities


def generate_timeslots(doctors, start_date=None, end_date=None):
    """Generate timeslots for doctors based on their availability"""
    
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    
    generated_count = 0
    for doctor in doctors:
        timeslots = Timeslot.generate_for_doctor(doctor, start_date, end_date)
        generated_count += len(timeslots)
    return generated_count


def create_wallets(users):
    """Create wallets for patient users"""
    
    patients = [u for u in users if u.role == 'patient']
    created_wallets = []
    
    for patient in patients:
        wallet, created = Wallet.objects.get_or_create(
            user=patient,
            defaults={'balance': Decimal('500.00')}  # Give each patient $500
        )
        if created:
            created_wallets.append(wallet)
        else:
            created_wallets.append(wallet)
    
    return created_wallets


def create_appointments(doctors, users):
    """Create sample appointments"""
    
    patients = [u for u in users if u.role == 'patient']
    created_appointments = []
    
    # Get some available timeslots
    available_timeslots = Timeslot.objects.filter(
        is_booked=False,
        start_time__gte=datetime.now()
    ).order_by('start_time')[:5]
    
    for i, timeslot in enumerate(available_timeslots):
        if i < len(patients):
            patient = patients[i]
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                timeslot=timeslot,
                defaults={
                    'doctor': timeslot.doctor,
                    'status': 'scheduled',
                    'notes': f'Sample appointment for {patient.get_full_name()}',
                }
            )
            if created:
                created_appointments.append(appointment)
    
    return created_appointments


def create_comments(doctors, users):
    """Create sample comments/reviews"""
    
    patients = [u for u in users if u.role == 'patient']
    created_comments = []
    
    sample_comments = [
        {
            'title': 'Excellent care!',
            'description': 'Dr. Smith provided excellent care and was very thorough in explaining my condition.',
            'doctor_rating': 5,
            'is_anonymous': False,
        },
        {
            'title': 'Very professional',
            'description': 'Great bedside manner and professional approach. Highly recommended.',
            'doctor_rating': 4,
            'is_anonymous': False,
        },
        {
            'title': 'Outstanding service',
            'description': 'The doctor was knowledgeable and made me feel comfortable throughout the visit.',
            'doctor_rating': 5,
            'is_anonymous': True,
        },
    ]
    
    for i, doctor in enumerate(doctors):
        for j, comment_data in enumerate(sample_comments):
            if j < len(patients):
                patient = patients[j]
                comment, created = Comment.objects.get_or_create(
                    doctor=doctor,
                    user=patient,
                    defaults=comment_data
                )
                if created:
                    created_comments.append(comment)
    
    return created_comments


def main():
    """Main seeding function"""
    
    try:
        with transaction.atomic():
            # Create users
            users = create_users()

            # Create doctors
            doctors = create_doctors(users)

            # Create doctor availabilities
            availabilities = create_doctor_availabilities(doctors)

            # Generate timeslots
            timeslot_count = generate_timeslots(doctors)

            # Create wallets
            wallets = create_wallets(users)

            # Create appointments
            appointments = create_appointments(doctors, users)

            # Create comments
            comments = create_comments(doctors, users)
            
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        raise


if __name__ == '__main__':
    main()
