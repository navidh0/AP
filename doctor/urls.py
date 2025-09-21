from django.urls import path
from .views import (
    DoctorListView,
    DoctorDetailView,
    DoctorCreateView,
    TimeslotCreateView
)

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor-list'),

    # This line MUST exist
    path('add/', DoctorCreateView.as_view(), name='doctor-add'),

    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/timeslots/add/', TimeslotCreateView.as_view(), name='timeslot-add'),
]