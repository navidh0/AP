from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Min, Max
from django.db import transaction
from django.http import JsonResponse
import json

from .models import Appointment
from .services import send_appointment_confirmation_email_safe
from doctor.models import Doctor, Timeslot
from wallet.models import Wallet, Transaction


class DoctorListView(ListView):
    """View to display list of available doctors"""
    model = Doctor
    template_name = 'booking/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 12
    
    def get_queryset(self):
        """Filter available doctors and add search functionality"""
        queryset = Doctor.objects.available()
        
        # Search functionality - search by name or specialty
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.search(name=search_query, specialty=search_query)
        
        # Specialty filter
        specialty = self.request.GET.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        
        # Fee range filter
        min_fee = self.request.GET.get('min_fee')
        max_fee = self.request.GET.get('max_fee')
        
        if min_fee:
            try:
                queryset = queryset.filter(fee__gte=float(min_fee))
            except (ValueError, TypeError):
                pass
                
        if max_fee:
            try:
                queryset = queryset.filter(fee__lte=float(max_fee))
            except (ValueError, TypeError):
                pass
        
        # Rating filter
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(average_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass
            
        return queryset.select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['specialty_filter'] = self.request.GET.get('specialty', '')
        context['min_fee'] = self.request.GET.get('min_fee', '')
        context['max_fee'] = self.request.GET.get('max_fee', '')
        context['min_rating'] = self.request.GET.get('min_rating', '')
        
        # Get unique specialties for filter dropdown
        context['specialties'] = Doctor.objects.values_list('specialty', flat=True).distinct().order_by('specialty')
        
        # Get fee range for filter
        fee_range = Doctor.objects.aggregate(
            min_fee=Min('fee'),
            max_fee=Max('fee')
        )
        context['fee_range'] = fee_range
        
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
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient and timeslot is available"""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to book an appointment.')
            return redirect('users:login')
        
        if request.user.role != 'patient':
            messages.error(request, 'Only patients can book appointments.')
            return redirect('booking:doctor_list')
        
        # Check if timeslot is available
        doctor_id = kwargs.get('doctor_id')
        timeslot_id = kwargs.get('timeslot_id')
        
        if doctor_id and timeslot_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                timeslot = Timeslot.objects.get(id=timeslot_id, doctor=doctor)
                
                if timeslot.is_booked:
                    messages.error(request, 'This time slot is no longer available.')
                    return redirect('booking:doctor_detail', pk=doctor_id)
            except (Doctor.DoesNotExist, Timeslot.DoesNotExist):
                messages.error(request, 'Invalid doctor or timeslot.')
                return redirect('booking:doctor_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get doctor and timeslot from URL parameters
        doctor_id = self.kwargs.get('doctor_id')
        timeslot_id = self.kwargs.get('timeslot_id')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        timeslot = get_object_or_404(Timeslot, id=timeslot_id, doctor=doctor)
        
        context['doctor'] = doctor
        context['timeslot'] = timeslot
        context['patient'] = self.request.user
        context['timeslot_available'] = not timeslot.is_booked
        
        return context
    
    def form_valid(self, form):
        """Set the patient, doctor, and timeslot for the appointment and process payment"""
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
        
        # Get or create wallet for the patient
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        
        # Check if wallet has sufficient funds
        if not wallet.has_sufficient_funds(doctor.fee):
            messages.error(
                self.request, 
                f'Insufficient funds in your wallet. Required: ${doctor.fee}, Available: ${wallet.balance}. Please add funds to your wallet first.'
            )
            return redirect('wallet:wallet_detail')
        
        # Process payment and create appointment
        try:
            with transaction.atomic():
                # Deduct funds from wallet
                new_balance = wallet.deduct_funds(doctor.fee)
                
                # Create transaction record
                payment_transaction = Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='payment',
                    amount=doctor.fee,
                    description=f'Payment for appointment with Dr. {doctor.user.get_full_name()}',
                    balance_after=new_balance
                )
                
                # Set appointment details
                form.instance.patient = self.request.user
                form.instance.doctor = doctor
                form.instance.timeslot = timeslot
                form.instance.status = 'confirmed'  # Mark as confirmed after payment
                
                # Save the appointment
                response = super().form_valid(form)
                
                # Link transaction to appointment
                payment_transaction.appointment = form.instance
                payment_transaction.save()
                
                # Create notification for successful booking
                from core.models import Notification
                Notification.create_notification(
                    user=self.request.user,
                    notification_type='appointment_booked',
                    title='Appointment Booked Successfully',
                    message=f'Your appointment with Dr. {doctor.user.get_full_name()} has been booked for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}. Payment of ${doctor.fee} has been processed.',
                    appointment=form.instance
                )
                
                # Send confirmation email after successful booking
                email_sent = send_appointment_confirmation_email_safe(form.instance)
                
                if email_sent:
                    messages.success(
                        self.request, 
                        f'Appointment booked and confirmed for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}. Payment of ${doctor.fee} processed. A confirmation email has been sent to your email address.'
                    )
                else:
                    messages.success(
                        self.request, 
                        f'Appointment booked and confirmed for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}. Payment of ${doctor.fee} processed. Note: Confirmation email could not be sent.'
                    )
                
                return response
                
        except Exception as e:
            messages.error(self.request, f'Payment processing failed: {str(e)}')
            return redirect('booking:doctor_detail', pk=doctor_id)
    
    def get_success_url(self):
        """Redirect to success page with the created appointment ID"""
        return reverse_lazy('booking:appointment_success', kwargs={'appointment_id': self.object.id})


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
    
    def get_context_data(self, **kwargs):
        """Add the specific appointment to context"""
        context = super().get_context_data(**kwargs)
        appointment_id = self.kwargs.get('appointment_id')
        
        if appointment_id:
            # Get the specific appointment that was just created
            specific_appointment = Appointment.objects.filter(
                id=appointment_id,
                patient=self.request.user
            ).select_related('doctor', 'timeslot').first()
            
            if specific_appointment:
                context['specific_appointment'] = specific_appointment
            else:
                # If specific appointment not found, use the first one from queryset
                context['specific_appointment'] = context['appointments'].first()
        else:
            # If no appointment ID, use the first one from queryset
            context['specific_appointment'] = context['appointments'].first()
        
        return context


class PatientAppointmentListView(LoginRequiredMixin, ListView):
    """View to display patient's appointment history (past and future)"""
    model = Appointment
    template_name = 'booking/patient_appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to view appointments.')
            return redirect('users:login')
        
        if request.user.role != 'patient':
            messages.error(request, 'Only patients can view appointment history.')
            return redirect('booking:doctor_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Get user's appointments divided into past and future"""
        now = timezone.now()
        
        # Get all appointments for the patient
        appointments = Appointment.objects.filter(
            patient=self.request.user
        ).select_related('doctor__user', 'timeslot').order_by('-timeslot__start_time')
        
        return appointments
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        from datetime import timedelta
        
        # Separate appointments into past and future
        all_appointments = self.get_queryset()
        
        future_appointments = all_appointments.filter(
            timeslot__start_time__gte=now
        ).order_by('timeslot__start_time')
        
        past_appointments = all_appointments.filter(
            timeslot__start_time__lt=now
        ).order_by('-timeslot__start_time')
        
        # Add cancellation eligibility for each future appointment
        for appointment in future_appointments:
            time_until_appointment = appointment.timeslot.start_time - now
            appointment.can_cancel = (
                appointment.status in ['scheduled', 'confirmed'] and 
                time_until_appointment > timedelta(hours=24)
            )
        
        # Get or create wallet for the user
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        
        context['future_appointments'] = future_appointments
        context['past_appointments'] = past_appointments
        context['has_future_appointments'] = future_appointments.exists()
        context['has_past_appointments'] = past_appointments.exists()
        context['wallet'] = wallet
        
        return context


class CancelAppointmentView(LoginRequiredMixin, View):
    """View to cancel an appointment"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to cancel appointments.')
            return redirect('users:login')
        
        if request.user.role != 'patient':
            messages.error(request, 'Only patients can cancel appointments.')
            return redirect('booking:doctor_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, appointment_id):
        """Cancel the appointment and process refund if applicable"""
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id, 
            patient=request.user
        )
        
        # Check if appointment can be cancelled (not already cancelled or completed)
        if appointment.status in ['cancelled', 'completed']:
            messages.error(request, 'This appointment cannot be cancelled.')
            return redirect('booking:patient_appointment_list')
        
        # Check if appointment is within 24 hours
        from datetime import timedelta
        time_until_appointment = appointment.timeslot.start_time - timezone.now()
        
        if time_until_appointment <= timedelta(hours=24):
            messages.error(request, 'Appointments can only be cancelled more than 24 hours in advance.')
            return redirect('booking:patient_appointment_list')
        
        try:
            with transaction.atomic():
                # Get wallet and process refund
                wallet = Wallet.objects.get(user=request.user)
                
                # Create refund transaction
                refund_transaction = Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='refund',
                    amount=appointment.doctor.fee,
                    description=f'Refund for cancelled appointment with Dr. {appointment.doctor.user.get_full_name()}',
                    balance_after=wallet.balance + appointment.doctor.fee,
                    appointment=appointment
                )
                
                # Add refund to wallet
                wallet.add_funds(appointment.doctor.fee)
                
                # Cancel the appointment
                appointment.cancel()
                
                # Create notification for cancellation and refund
                from core.models import Notification
                Notification.create_notification(
                    user=request.user,
                    notification_type='appointment_cancelled',
                    title='Appointment Cancelled',
                    message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been cancelled. A refund of ${appointment.doctor.fee} has been processed to your wallet.',
                    appointment=appointment
                )
                
                # Create notification for refund
                Notification.create_notification(
                    user=request.user,
                    notification_type='refund_processed',
                    title='Refund Processed',
                    message=f'Refund of ${appointment.doctor.fee} has been added to your wallet for the cancelled appointment with Dr. {appointment.doctor.user.get_full_name()}.',
                    appointment=appointment
                )
                
                messages.success(
                    request, 
                    f'Appointment cancelled successfully. Refund of ${appointment.doctor.fee} has been added to your wallet.'
                )
                
        except Exception as e:
            messages.error(request, f'Failed to cancel appointment: {str(e)}')
        
        return redirect('booking:patient_appointment_list')


class BookAppointmentAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint for booking appointments"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'})
        
        if request.user.role != 'patient':
            return JsonResponse({'success': False, 'error': 'Only patients can book appointments'})
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
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
            
            # Send confirmation email after successful booking
            email_sent = send_appointment_confirmation_email_safe(appointment)
            
            if email_sent:
                message = f'Appointment booked successfully for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}. A confirmation email has been sent to your email address.'
            else:
                message = f'Appointment booked successfully for {timeslot.start_time.strftime("%B %d, %Y at %I:%M %p")}. Note: Confirmation email could not be sent.'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'appointment_id': appointment.id,
                'email_sent': email_sent
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
