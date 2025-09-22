import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from doctor.models import Doctor
from django.test import RequestFactory
from booking.views import DoctorListView

print("Testing Booking Search Functionality")
print("=" * 50)

# Test 1: Check if doctors exist
print("1. Checking available doctors:")
doctors = Doctor.objects.available()
print(f"   Total available doctors: {doctors.count()}")
for doctor in doctors:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n2. Testing search method directly:")
# Test search method
search_results = Doctor.objects.available().search(name='smith')
print(f"   Search for 'smith': {search_results.count()} results")
for doctor in search_results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

search_results = Doctor.objects.available().search(name='dr')
print(f"   Search for 'dr': {search_results.count()} results")
for doctor in search_results:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n3. Testing view with search query:")
# Test the view with search
factory = RequestFactory()
request = factory.get('/booking/doctors/', {'search': 'smith'})
view = DoctorListView()
view.request = request
queryset = view.get_queryset()
print(f"   View search for 'smith': {queryset.count()} results")
for doctor in queryset:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n4. Testing view with specialty filter:")
request = factory.get('/booking/doctors/', {'specialty': 'cardiology'})
view = DoctorListView()
view.request = request
queryset = view.get_queryset()
print(f"   View specialty filter for 'cardiology': {queryset.count()} results")
for doctor in queryset:
    print(f"   - {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})")

print("\n" + "=" * 50)
print("Search test completed!")
