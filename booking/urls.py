from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Doctor listing and detail views
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    
    # Appointment booking
    path('book/<int:doctor_id>/<int:timeslot_id>/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('success/', views.AppointmentSuccessView.as_view(), name='appointment_success'),
    
    # AJAX endpoints
    path('api/book/', views.book_appointment_ajax, name='book_appointment_ajax'),
]
