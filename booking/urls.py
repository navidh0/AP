from django.urls import path
from . import views

app_name = 'booking'
urlpatterns = [
    # Doctor listing and detail views
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    
    # Appointment booking
    path('book/<int:doctor_id>/<int:timeslot_id>/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('success/<int:appointment_id>/', views.AppointmentSuccessView.as_view(), name='appointment_success'),
    
    # Patient appointment history
    path('my-appointments/', views.PatientAppointmentListView.as_view(), name='patient_appointment_list'),
    
    # Appointment cancellation
    path('cancel/<int:appointment_id>/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    
    # AJAX endpoints
    path('api/book/', views.BookAppointmentAjaxView.as_view(), name='book_appointment_ajax'),
]

