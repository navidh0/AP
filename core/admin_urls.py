from django.urls import path
from . import admin_views

app_name = 'admin_dashboard'

urlpatterns = [
    path('dashboard/', admin_views.AdminDashboardView.as_view(), name='dashboard'),
    path('doctors/', admin_views.ManageDoctorsView.as_view(), name='manage_doctors'),
    path('doctors/<int:doctor_id>/verify/', admin_views.VerifyDoctorView.as_view(), name='verify_doctor'),
    path('doctors/<int:doctor_id>/reject/', admin_views.RejectDoctorView.as_view(), name='reject_doctor'),
    path('doctors/<int:doctor_id>/suspend/', admin_views.SuspendDoctorView.as_view(), name='suspend_doctor'),
    path('doctors/<int:doctor_id>/toggle-availability/', admin_views.ToggleDoctorAvailabilityView.as_view(), name='toggle_doctor_availability'),
    path('funding-requests/', admin_views.ManageFundingRequestsView.as_view(), name='manage_funding_requests'),
    path('funding-requests/<int:request_id>/approve/', admin_views.ApproveFundingRequestView.as_view(), name='approve_funding_request'),
    path('funding-requests/<int:request_id>/reject/', admin_views.RejectFundingRequestView.as_view(), name='reject_funding_request'),
    path('profile-changes/', admin_views.ManageProfileChangesView.as_view(), name='manage_profile_changes'),
    path('profile-changes/<int:change_id>/approve/', admin_views.ApproveProfileChangeView.as_view(), name='approve_profile_change'),
    path('profile-changes/<int:change_id>/reject/', admin_views.RejectProfileChangeView.as_view(), name='reject_profile_change'),
]
