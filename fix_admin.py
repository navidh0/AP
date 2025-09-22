#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from users.models import User

# Check admin user
try:
    admin = User.objects.get(username='admin')
    print(f"Admin user found:")
    print(f"  Username: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Is active: {admin.is_active}")
    print(f"  Is staff: {admin.is_staff}")
    print(f"  Is superuser: {admin.is_superuser}")
    print(f"  Role: {admin.role}")
    print(f"  SSN: {admin.ssn}")
    
    # Check password
    password_check = admin.check_password('admin123')
    print(f"  Password 'admin123' works: {password_check}")
    
    # Fix admin user if needed
    if not admin.is_staff or not admin.is_superuser or admin.role != 'admin':
        print("\nFixing admin user...")
        admin.is_staff = True
        admin.is_superuser = True
        admin.role = 'admin'
        admin.is_active = True
        admin.save()
        print("Admin user fixed!")
    
    # Set password
    admin.set_password('admin123')
    admin.save()
    print("Password set to 'admin123'")
    
    # Verify
    print(f"\nFinal verification:")
    print(f"  Is staff: {admin.is_staff}")
    print(f"  Is superuser: {admin.is_superuser}")
    print(f"  Role: {admin.role}")
    print(f"  Password check: {admin.check_password('admin123')}")
    
except User.DoesNotExist:
    print("Admin user not found. Creating new admin user...")
    admin = User.objects.create_user(
        username='admin',
        email='admin@medicare.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        phone_number='+989123456789',
        ssn='0000000001',
        role='admin',
        is_active=True,
        is_staff=True,
        is_superuser=True,
        is_email_verified=True,
        is_phone_verified=True,
        birth_date='1980-01-01',
        gender='male'
    )
    print("Admin user created successfully!")
