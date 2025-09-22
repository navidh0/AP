import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from doctor.models import Doctor

print("Testing booking search functionality...")
print("=" * 50)

# Test 1: Basic search
print("1. Testing search for 'smith':")
results = Doctor.objects.available().search(name='smith')
print(f"   Found {results.count()} doctors")
for doctor in results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n2. Testing search for 'cardiology':")
results = Doctor.objects.available().search(specialty='cardiology')
print(f"   Found {results.count()} doctors")
for doctor in results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n3. Testing search for 'dr':")
results = Doctor.objects.available().search(name='dr')
print(f"   Found {results.count()} doctors")
for doctor in results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n4. Testing all available doctors:")
results = Doctor.objects.available()
print(f"   Found {results.count()} available doctors")
for doctor in results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty}) - Available: {doctor.availability}")

print("\n5. Testing search with both name and specialty:")
results = Doctor.objects.available().search(name='smith', specialty='cardiology')
print(f"   Found {results.count()} doctors")
for doctor in results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n" + "=" * 50)
print("Search test completed!")
