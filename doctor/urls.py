from django.urls import path
from .views import (
    DoctorListView,
    DoctorDetailView,
    DoctorCreateView,
    TimeslotCreateView,
    CommentCreateView,
    DoctorAvailabilityCreateView,
    TimeslotListView,
    GenerateTimeslotsAjaxView
)
from . import dashboard_views

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor-list'),

    # This line MUST exist
    path('add/', DoctorCreateView.as_view(), name='doctor-add'),

    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/timeslots/add/', TimeslotCreateView.as_view(), name='timeslot-add'),
    path('<int:doctor_id>/comment/add/', CommentCreateView.as_view(), name='comment-add'),
    
    # Availability management
    path('availability/add/', DoctorAvailabilityCreateView.as_view(), name='availability-add'),
    path('<int:doctor_id>/timeslots/', TimeslotListView.as_view(), name='timeslot-list'),
    path('<int:doctor_id>/generate-timeslots/', GenerateTimeslotsAjaxView.as_view(), name='generate-timeslots-ajax'),
    
    # Doctor Dashboard URLs
    path('dashboard/', dashboard_views.DoctorDashboardView.as_view(), name='dashboard'),
    path('dashboard/appointments/', dashboard_views.DoctorAppointmentsView.as_view(), name='dashboard-appointments'),
    path('dashboard/timeslots/', dashboard_views.DoctorTimeslotsView.as_view(), name='dashboard-timeslots'),
    path('dashboard/day-offs/', dashboard_views.DoctorDayOffsView.as_view(), name='dashboard-day-offs'),
    path('dashboard/profile/', dashboard_views.DoctorProfileView.as_view(), name='dashboard-profile'),
    path('dashboard/request-day-off/', dashboard_views.RequestDayOffView.as_view(), name='request-day-off'),
    path('dashboard/cancel-day-off/<int:day_off_id>/', dashboard_views.CancelDayOffView.as_view(), name='cancel-day-off'),
    path('dashboard/request-profile-change/', dashboard_views.RequestProfileChangeView.as_view(), name='request-profile-change'),
]