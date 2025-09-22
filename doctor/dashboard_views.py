from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.views.generic import TemplateView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
import json

from .models import Doctor, DoctorAvailability, Timeslot, DayOff, ProfileChangeRequest
from booking.models import Appointment
from wallet.models import Wallet, Transaction


class DoctorRequiredMixin(UserPassesTestMixin):
    """Mixin to require doctor access"""
    def test_func(self):
        return (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'doctor_profile') and
                self.request.user.doctor_profile.verification_status == 'verified')
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'doctor_profile'):
            # Doctor profile exists but not verified
            from django.shortcuts import render
            return render(self.request, 'doctor/verification_pending.html', {
                'verification_status': self.request.user.doctor_profile.verification_status
            })
        return super().handle_no_permission()


class DoctorDashboardView(DoctorRequiredMixin, TemplateView):
    """Doctor dashboard overview"""
    template_name = 'doctor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            timeslot__start_time__gte=timezone.now()
        ).select_related('patient', 'timeslot').order_by('timeslot__start_time')[:10]
        
        # Get today's appointments
        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(
            doctor=doctor,
            timeslot__start_time__date=today
        ).select_related('patient', 'timeslot').order_by('timeslot__start_time')
        
        
        # Get pending profile change requests
        pending_profile_changes = ProfileChangeRequest.objects.filter(
            doctor=doctor,
            status='pending'
        ).order_by('-requested_at')
        
        # Get or create doctor's wallet
        wallet, created = Wallet.objects.get_or_create(user=doctor.user)
        
        # Calculate income from completed appointments
        completed_appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=['completed', 'confirmed']
        )
        total_income = sum(appointment.doctor.fee for appointment in completed_appointments)
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:10]
        
        # Get statistics
        stats = {
            'total_appointments': Appointment.objects.filter(doctor=doctor).count(),
            'today_appointments': today_appointments.count(),
            'upcoming_appointments': upcoming_appointments.count(),
            'pending_profile_changes': pending_profile_changes.count(),
            'total_income': total_income,
            'wallet_balance': wallet.balance,
        }
        
        context.update({
            'doctor': doctor,
            'upcoming_appointments': upcoming_appointments,
            'today_appointments': today_appointments,
            'pending_profile_changes': pending_profile_changes,
            'wallet': wallet,
            'total_income': total_income,
            'recent_transactions': recent_transactions,
            'stats': stats,
        })
        return context


class DoctorAppointmentsView(DoctorRequiredMixin, ListView):
    """View all doctor appointments"""
    model = Appointment
    template_name = 'doctor/appointments.html'
    context_object_name = 'appointments'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter appointments by status and date"""
        doctor = self.request.user.doctor_profile
        queryset = Appointment.objects.filter(doctor=doctor).select_related('patient', 'timeslot')
        
        # Filter by status
        status_filter = self.request.GET.get('status', 'all')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date
        date_filter = self.request.GET.get('date', '')
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(timeslot__start_time__date=filter_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timeslot__start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_date'] = self.request.GET.get('date', '')
        return context


class DoctorTimeslotsView(DoctorRequiredMixin, TemplateView):
    """Manage doctor timeslots"""
    template_name = 'doctor/timeslots.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get availabilities
        availabilities = DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
        
        # Get timeslots
        timeslots = Timeslot.objects.filter(doctor=doctor).order_by('-start_time')
        
        context.update({
            'doctor': doctor,
            'availabilities': availabilities,
            'timeslots': timeslots,
        })
        return context


class RequestProfileChangeView(DoctorRequiredMixin, View):
    """Request a profile change"""
    
    def post(self, request):
        doctor = request.user.doctor_profile
        
        try:
            data = json.loads(request.body)
            field_name = data.get('field_name')
            new_value = data.get('new_value')
            reason = data.get('reason', '')
            
            if not all([field_name, new_value, reason]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})
            
            # Get current value
            old_value = str(getattr(doctor, field_name, ''))
            
            # Check if change is actually different
            if old_value == str(new_value):
                return JsonResponse({'success': False, 'error': 'New value is the same as current value'})
            
            # Create profile change request
            change_request = ProfileChangeRequest.objects.create(
                doctor=doctor,
                field_name=field_name,
                old_value=old_value,
                new_value=str(new_value),
                reason=reason
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Profile change request for {field_name} submitted successfully',
                'request_id': change_request.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class DoctorProfileView(DoctorRequiredMixin, TemplateView):
    """Manage doctor profile"""
    template_name = 'doctor/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get pending profile change requests
        pending_changes = ProfileChangeRequest.objects.filter(
            doctor=doctor,
            status='pending'
        ).order_by('-requested_at')
        
        context.update({
            'doctor': doctor,
            'pending_changes': pending_changes,
        })
        return context


class DoctorDayOffsView(DoctorRequiredMixin, ListView):
    """View and manage doctor's day offs"""
    model = DayOff
    template_name = 'doctor/day_offs.html'
    context_object_name = 'day_offs'
    paginate_by = 20
    
    def get_queryset(self):
        doctor = self.request.user.doctor_profile
        return DayOff.objects.filter(doctor=doctor).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get upcoming day offs
        upcoming_day_offs = DayOff.objects.filter(
            doctor=doctor,
            date__gte=timezone.now().date()
        ).order_by('date')
        
        # Get past day offs
        past_day_offs = DayOff.objects.filter(
            doctor=doctor,
            date__lt=timezone.now().date()
        ).order_by('-date')
        
        context.update({
            'doctor': doctor,
            'upcoming_day_offs': upcoming_day_offs,
            'past_day_offs': past_day_offs,
        })
        return context


class RequestDayOffView(DoctorRequiredMixin, View):
    """Request a day off and delete timeslots for that date"""
    
    def post(self, request):
        doctor = request.user.doctor_profile
        date_str = request.POST.get('date')
        reason = request.POST.get('reason', '')
        
        if not date_str:
            messages.error(request, 'Please select a date for your day off.')
            return redirect('doctor:dashboard-day-offs')
        
        try:
            from datetime import datetime
            day_off_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('doctor:dashboard-day-offs')
        
        # Check if date is in the past
        if day_off_date < timezone.now().date():
            messages.error(request, 'Cannot request a day off for a past date.')
            return redirect('doctor:dashboard-day-offs')
        
        # Check if day off already exists
        if DayOff.objects.filter(doctor=doctor, date=day_off_date).exists():
            messages.error(request, 'You have already requested a day off for this date.')
            return redirect('doctor:dashboard-day-offs')
        
        # Create day off request
        day_off = DayOff.objects.create(
            doctor=doctor,
            date=day_off_date,
            reason=reason,
            is_approved=True  # Auto-approve for now, can be changed to require admin approval
        )
        
        # Delete timeslots for this date and handle refunds
        deleted_count, refunded_appointments = day_off.delete_timeslots_for_date()
        
        # Create success message
        if refunded_appointments:
            messages.success(
                request, 
                f'Day off requested for {day_off_date}. {deleted_count} timeslots removed. {len(refunded_appointments)} patients have been notified and refunded.'
            )
        else:
            messages.success(
                request, 
                f'Day off requested for {day_off_date}. {deleted_count} timeslots have been removed.'
            )
        
        return redirect('doctor:dashboard-day-offs')


class CancelDayOffView(DoctorRequiredMixin, View):
    """Cancel a day off request"""
    
    def post(self, request, day_off_id):
        doctor = request.user.doctor_profile
        
        try:
            day_off = DayOff.objects.get(id=day_off_id, doctor=doctor)
            day_off_date = day_off.date
            day_off.delete()
            
            messages.success(request, f'Day off for {day_off_date} has been cancelled.')
        except DayOff.DoesNotExist:
            messages.error(request, 'Day off not found.')
        
        return redirect('doctor:dashboard-day-offs')
