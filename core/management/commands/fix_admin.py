from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Fix admin user for login'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
            self.stdout.write(f"Admin user found: {admin.username}")
            
            # Fix admin user
            admin.is_staff = True
            admin.is_superuser = True
            admin.role = 'admin'
            admin.is_active = True
            admin.ssn = '0000000001'
            admin.save()
            
            # Set password
            admin.set_password('admin123')
            admin.save()
            
            self.stdout.write(
                self.style.SUCCESS('Admin user fixed successfully!')
            )
            self.stdout.write(f"Username: {admin.username}")
            self.stdout.write(f"Password: admin123")
            self.stdout.write(f"Is staff: {admin.is_staff}")
            self.stdout.write(f"Is superuser: {admin.is_superuser}")
            self.stdout.write(f"Role: {admin.role}")
            
        except User.DoesNotExist:
            self.stdout.write("Admin user not found. Creating new one...")
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
            self.stdout.write(
                self.style.SUCCESS('Admin user created successfully!')
            )
