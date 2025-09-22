from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.generic import TemplateView, ListView
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
import json

from users.models import User
from doctor.models import Doctor, DoctorAvailability, Timeslot, DayOff, ProfileChangeRequest
from booking.models import Appointment
from wallet.models import Wallet, Transaction, FundingRequest


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access"""
    def test_func(self):
        return self.request.user.is_staff


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """Admin dashboard overview"""
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get statistics
        stats = {
            'total_patients': User.objects.filter(role='patient').count(),
            'total_doctors': Doctor.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'pending_funding_requests': FundingRequest.objects.filter(status='pending').count(),
            'pending_doctor_verifications': Doctor.objects.filter(verification_status='pending').count(),
            'pending_profile_changes': ProfileChangeRequest.objects.filter(status='pending').count(),
            'total_wallet_balance': sum(Wallet.objects.values_list('balance', flat=True)),
            'pending_requests': FundingRequest.objects.select_related('user').filter(status='pending').order_by('-requested_at')[:5],
            'pending_doctors': Doctor.objects.select_related('user').filter(verification_status='pending').order_by('-created_at')[:5],
            'pending_profile_changes_list': ProfileChangeRequest.objects.select_related('doctor__user').filter(status='pending').order_by('-requested_at')[:5],
        }
        context['stats'] = stats
        return context




class ManageDoctorsView(StaffRequiredMixin, ListView):
    """Manage doctors - approve/reject doctor registrations"""
    model = Doctor
    template_name = 'admin/manage_doctors.html'
    context_object_name = 'doctors'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter doctors by verification status"""
        queryset = Doctor.objects.select_related('user').order_by('-created_at')
        status = self.request.GET.get('status', 'all')
        if status != 'all':
            queryset = queryset.filter(verification_status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        return context


class ManageTimeslotsView(StaffRequiredMixin, ListView):
    """Manage doctor timeslots"""
    model = Timeslot
    template_name = 'admin/manage_timeslots.html'
    context_object_name = 'timeslots'
    paginate_by = 20
    
    def get_queryset(self):
        return Timeslot.objects.select_related('doctor__user').order_by('-start_time')


class ManageFundingRequestsView(StaffRequiredMixin, ListView):
    """Manage funding requests"""
    model = FundingRequest
    template_name = 'admin/manage_funding_requests.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter funding requests by status"""
        queryset = FundingRequest.objects.select_related('user').order_by('-requested_at')
        status = self.request.GET.get('status', 'pending')
        if status != 'all':
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'pending')
        return context


class ApproveFundingRequestView(StaffRequiredMixin, View):
    """Approve a funding request"""
    
    def post(self, request, request_id):
        funding_request = get_object_or_404(FundingRequest, id=request_id)
        
        if funding_request.status != 'pending':
            messages.error(request, 'This request has already been processed.')
            return redirect('admin_dashboard:manage_funding_requests')
        
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            success = funding_request.approve(request.user, admin_notes)
            
            if success:
                messages.success(request, f'Funding request for ${funding_request.amount} approved successfully.')
            else:
                messages.error(request, 'Failed to approve funding request.')
                
        except Exception as e:
            messages.error(request, f'Error approving request: {str(e)}')
        
        return redirect('admin_dashboard:manage_funding_requests')


class RejectFundingRequestView(StaffRequiredMixin, View):
    """Reject a funding request"""
    
    def post(self, request, request_id):
        funding_request = get_object_or_404(FundingRequest, id=request_id)
        
        if funding_request.status != 'pending':
            messages.error(request, 'This request has already been processed.')
            return redirect('admin_dashboard:manage_funding_requests')
        
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            success = funding_request.reject(request.user, admin_notes)
            
            if success:
                messages.success(request, f'Funding request for ${funding_request.amount} rejected.')
            else:
                messages.error(request, 'Failed to reject funding request.')
                
        except Exception as e:
            messages.error(request, f'Error rejecting request: {str(e)}')
        
        return redirect('admin_dashboard:manage_funding_requests')


class ViewTransactionsView(StaffRequiredMixin, ListView):
    """View all transactions"""
    model = Transaction
    template_name = 'admin/view_transactions.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        return Transaction.objects.select_related('wallet__user', 'appointment').order_by('-created_at')


class ViewAppointmentsView(StaffRequiredMixin, ListView):
    """View all appointments"""
    model = Appointment
    template_name = 'admin/view_appointments.html'
    context_object_name = 'appointments'
    paginate_by = 50
    
    def get_queryset(self):
        return Appointment.objects.select_related('patient', 'doctor__user', 'timeslot').order_by('-created_at')


class VerifyDoctorView(StaffRequiredMixin, View):
    """Verify a doctor"""
    
    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        if doctor.verification_status not in ['pending', 'rejected']:
            messages.error(request, 'This doctor cannot be verified in their current status.')
            return redirect('admin_dashboard:manage_doctors')
        
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            # Store original status for message
            original_status = doctor.verification_status
            success = doctor.verify(request.user, admin_notes)
            
            if success:
                if original_status == 'pending':
                    messages.success(request, f'Dr. {doctor.user.get_full_name()} has been verified successfully.')
                else:  # rejected
                    messages.success(request, f'Dr. {doctor.user.get_full_name()} has been re-verified successfully.')
            else:
                messages.error(request, 'Failed to verify doctor.')
                
        except Exception as e:
            messages.error(request, f'Error verifying doctor: {str(e)}')
        
        return redirect('admin_dashboard:manage_doctors')


class RejectDoctorView(StaffRequiredMixin, View):
    """Reject doctor verification"""
    
    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        if doctor.verification_status not in ['pending', 'verified']:
            messages.error(request, 'This doctor cannot be rejected in their current status.')
            return redirect('admin_dashboard:manage_doctors')
        
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            if doctor.verification_status == 'pending':
                success = doctor.reject_verification(request.user, admin_notes)
                action = 'verification has been rejected'
            else:  # verified
                success = doctor.reject_verification(request.user, admin_notes)
                action = 'has been rejected and moved to rejected status'
            
            if success:
                messages.success(request, f'Dr. {doctor.user.get_full_name()} {action}.')
            else:
                messages.error(request, 'Failed to reject doctor.')
                
        except Exception as e:
            messages.error(request, f'Error rejecting doctor: {str(e)}')
        
        return redirect('admin_dashboard:manage_doctors')


class SuspendDoctorView(StaffRequiredMixin, View):
    """Suspend a doctor"""
    
    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            success = doctor.suspend(request.user, admin_notes)
            
            if success:
                messages.success(request, f'Dr. {doctor.user.get_full_name()} has been suspended.')
            else:
                messages.error(request, 'Failed to suspend doctor.')
                
        except Exception as e:
            messages.error(request, f'Error suspending doctor: {str(e)}')
        
        return redirect('admin_dashboard:manage_doctors')


class ToggleDoctorAvailabilityView(StaffRequiredMixin, View):
    """Toggle doctor availability"""
    
    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        try:
            new_availability = doctor.toggle_availability()
            status = "available" if new_availability else "unavailable"
            messages.success(request, f'Dr. {doctor.user.get_full_name()} is now {status}.')
        except Exception as e:
            messages.error(request, f'Error toggling availability: {str(e)}')
        
        return redirect('admin_dashboard:manage_doctors')


class ManageDayOffsView(StaffRequiredMixin, ListView):
    """Manage doctor day off requests"""
    model = DayOff
    template_name = 'admin/manage_day_offs.html'
    context_object_name = 'day_offs'
    paginate_by = 20
    
    def get_queryset(self):
        return DayOff.objects.select_related('doctor__user').order_by('-created_at')


class ApproveDayOffView(StaffRequiredMixin, View):
    """Approve a day off request"""
    
    def post(self, request, day_off_id):
        day_off = get_object_or_404(DayOff, id=day_off_id)
        
        if day_off.is_approved:
            messages.error(request, 'This day off request has already been approved.')
            return redirect('admin_dashboard:manage_day_offs')
        
        try:
            day_off.is_approved = True
            day_off.save()
            messages.success(request, f'Day off request for {day_off.doctor.user.get_full_name()} on {day_off.date} has been approved.')
        except Exception as e:
            messages.error(request, f'Error approving day off: {str(e)}')
        
        return redirect('admin_dashboard:manage_day_offs')


class RejectDayOffView(StaffRequiredMixin, View):
    """Reject a day off request"""
    
    def post(self, request, day_off_id):
        day_off = get_object_or_404(DayOff, id=day_off_id)
        
        if day_off.is_approved:
            messages.error(request, 'This day off request has already been approved.')
            return redirect('admin_dashboard:manage_day_offs')
        
        try:
            day_off.delete()
            messages.success(request, f'Day off request for {day_off.doctor.user.get_full_name()} on {day_off.date} has been rejected and deleted.')
        except Exception as e:
            messages.error(request, f'Error rejecting day off: {str(e)}')
        
        return redirect('admin_dashboard:manage_day_offs')


class ManageProfileChangesView(StaffRequiredMixin, ListView):
    """Manage doctor profile change requests"""
    model = ProfileChangeRequest
    template_name = 'admin/manage_profile_changes.html'
    context_object_name = 'profile_changes'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter profile changes by status"""
        queryset = ProfileChangeRequest.objects.select_related('doctor__user').order_by('-requested_at')
        status = self.request.GET.get('status', 'all')
        if status != 'all':
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        return context


class ApproveProfileChangeView(StaffRequiredMixin, View):
    """Approve a profile change request"""
    
    def post(self, request, change_id):
        change = get_object_or_404(ProfileChangeRequest, id=change_id)
        
        if change.status != 'pending':
            messages.error(request, 'This profile change request has already been processed.')
            return redirect('admin_dashboard:manage_profile_changes')
        
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            success = change.approve(request.user, admin_notes)
            
            if success:
                messages.success(request, f'Profile change request for {change.doctor.user.get_full_name()} has been approved.')
            else:
                messages.error(request, 'Failed to approve profile change request.')
                
        except Exception as e:
            messages.error(request, f'Error approving profile change: {str(e)}')
        
        return redirect('admin_dashboard:manage_profile_changes')


class RejectProfileChangeView(StaffRequiredMixin, View):
    """Reject a profile change request"""
    
    def post(self, request, change_id):
        change = get_object_or_404(ProfileChangeRequest, id=change_id)
        
        if change.status != 'pending':
            messages.error(request, 'This profile change request has already been processed.')
            return redirect('admin_dashboard:manage_profile_changes')
        
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body) if request.body else {}
                admin_notes = data.get('admin_notes', '')
            else:
                admin_notes = request.POST.get('admin_notes', '')
            
            success = change.reject(request.user, admin_notes)
            
            if success:
                messages.success(request, f'Profile change request for {change.doctor.user.get_full_name()} has been rejected.')
            else:
                messages.error(request, 'Failed to reject profile change request.')
                
        except Exception as e:
            messages.error(request, f'Error rejecting profile change: {str(e)}')
        
        return redirect('admin_dashboard:manage_profile_changes')
