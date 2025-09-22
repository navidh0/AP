import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from users.models import User

# Get or create admin user
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@medicare.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'phone_number': '+989123456789',
        'ssn': '0000000001',
        'role': 'admin',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
        'is_email_verified': True,
        'is_phone_verified': True,
        'birth_date': '1980-01-01',
        'gender': 'male'
    }
)

if not created:
    # Update existing admin
    admin.is_active = True
    admin.is_staff = True
    admin.is_superuser = True
    admin.role = 'admin'
    admin.ssn = '0000000001'
    admin.save()

# Set password
admin.set_password('admin123')
admin.save()

print(f"Admin user {'created' if created else 'updated'} successfully!")
print(f"Username: {admin.username}")
print(f"Password: admin123")
print(f"Is active: {admin.is_active}")
print(f"Is staff: {admin.is_staff}")
print(f"Is superuser: {admin.is_superuser}")
print(f"Role: {admin.role}")
print(f"Password check: {admin.check_password('admin123')}")
