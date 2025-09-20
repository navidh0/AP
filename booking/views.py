from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Appointment
from doctor.models import Doctor, Timeslot


class DoctorListView(ListView):
    """View to display list of available doctors"""
    model = Doctor
    template_name = 'booking/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 12
    
    def get_queryset(self):
        """Filter available doctors and add search functionality"""
        queryset = Doctor.objects.available()
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.search(name=search_query)
        
        # Specialty filter
        specialty = self.request.GET.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
            
        return queryset.select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['specialty_filter'] = self.request.GET.get('specialty', '')
        
        # Get unique specialties for filter dropdown
        context['specialties'] = Doctor.objects.values_list('specialty', flat=True).distinct().order_by('specialty')
        
        return context


class DoctorDetailView(DetailView):
    """View to display doctor details and available time slots"""
    model = Doctor
    template_name = 'booking/doctor_detail.html'
    context_object_name = 'doctor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.get_object()
        
        # Get available time slots for the next 30 days
        from datetime import timedelta
        start_date = timezone.now()
        end_date = start_date + timedelta(days=30)
        
        available_slots = Timeslot.objects.filter(
            doctor=doctor,
            is_booked=False,
            start_time__gte=start_date,
            start_time__lte=end_date
        ).order_by('start_time')
        
        context['available_slots'] = available_slots
        context['has_available_slots'] = available_slots.exists()
        
        return context


class AppointmentCreateView(LoginRequiredMixin, CreateView):
    """View to create a new appointment"""
    model = Appointment
    fields = ['notes']
    template_name = 'booking/appointment_create.html'
    success_url = reverse_lazy('booking:appointment_success')
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to book an appointment.')
            return redirect('users:login')
        
        if request.user.role != 'patient':
            messages.error(request, 'Only patients can book appointments.')
            return redirect('booking:doctor_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get doctor and timeslot from URL parameters
        doctor_id = self.kwargs.get('doctor_id')
        timeslot_id = self.kwargs.get('timeslot_id')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        timeslot = get_object_or_404(Timeslot, id=timeslot_id, doctor=doctor)
        
        # Verify timeslot is available
        if timeslot.is_booked:
            messages.error(self.request, 'This time slot is no longer available.')
            return redirect('booking:doctor_detail', pk=doctor_id)
        
        context['doctor'] = doctor
        context['timeslot'] = timeslot
        context['patient'] = self.request.user
        
        return context
    
    def form_valid(self, form):
        """Set the patient, doctor, and timeslot for the appointment"""
        doctor_id = self.kwargs.get('doctor_id')
        timeslot_id = self.kwargs.get('timeslot_id')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        timeslot = get_object_or_404(Timeslot, id=timeslot_id, doctor=doctor)
        
        # Check if timeslot is still available
        if timeslot.is_booked:
            messages.error(self.request, 'This time slot is no longer available.')
            return redirect('booking:doctor_detail', pk=doctor_id)
        
        # Check if patient already has an appointment at this time
        existing_appointment = Appointment.objects.filter(
            patient=self.request.user,
            timeslot=timeslot
        ).exists()
        
        if existing_appointment:
            messages.error(self.request, 'You already have an appointment at this time.')
            return redirect('booking:doctor_detail', pk=doctor_id)
        
        form.instance.patient = self.request.user
        form.instance.doctor = doctor
        form.instance.timeslot = timeslot
        
        messages.success(
            self.request, 
            f'Appointment booked successfully for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}'
        )
        
        return super().form_valid(form)


class AppointmentSuccessView(LoginRequiredMixin, ListView):
    """View to show appointment booking success"""
    model = Appointment
    template_name = 'booking/appointment_success.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        """Get user's upcoming appointments"""
        return Appointment.objects.filter(
            patient=self.request.user,
            status__in=['scheduled', 'confirmed'],
            timeslot__start_time__gte=timezone.now()
        ).select_related('doctor', 'timeslot').order_by('timeslot__start_time')


@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["POST"])
def book_appointment_ajax(request):
    """AJAX endpoint for booking appointments"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.user.role != 'patient':
        return JsonResponse({'success': False, 'error': 'Only patients can book appointments'})
    
    try:
        data = json.loads(request.body)
        timeslot_id = data.get('timeslot_id')
        
        if not timeslot_id:
            return JsonResponse({'success': False, 'error': 'Timeslot ID is required'})
        
        timeslot = get_object_or_404(Timeslot, id=timeslot_id)
        
        # Check if timeslot is available
        if timeslot.is_booked:
            return JsonResponse({'success': False, 'error': 'This time slot is no longer available'})
        
        # Check if patient already has an appointment at this time
        existing_appointment = Appointment.objects.filter(
            patient=request.user,
            timeslot=timeslot
        ).exists()
        
        if existing_appointment:
            return JsonResponse({'success': False, 'error': 'You already have an appointment at this time'})
        
        # Create appointment
        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=timeslot.doctor,
            timeslot=timeslot,
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Appointment booked successfully for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}',
            'appointment_id': appointment.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
