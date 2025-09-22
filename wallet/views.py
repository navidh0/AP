from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
import json

from .models import Wallet, Transaction, FundingRequest
from booking.models import Appointment


class WalletDetailView(LoginRequiredMixin, DetailView):
    """View to display patient's wallet details"""
    model = Wallet
    template_name = 'wallet/wallet_detail.html'
    context_object_name = 'wallet'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to view wallet.')
            return redirect('users:login')
        
        if request.user.role != 'patient':
            messages.error(request, 'Only patients can view wallet.')
            return redirect('booking:doctor_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        """Get or create wallet for the current user"""
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet = self.get_object()
        
        # Get recent transactions
        recent_transactions = wallet.transactions.all()[:10]
        context['recent_transactions'] = recent_transactions
        
        # Get pending funding requests
        pending_requests = FundingRequest.objects.filter(user=self.request.user, status='pending').order_by('-requested_at')
        context['pending_requests'] = pending_requests
        
        return context


class AddFundsAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to request funds addition to wallet (requires admin approval)"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'})
        
        if request.user.role != 'patient':
            return JsonResponse({'success': False, 'error': 'Only patients can request funds'})
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            description = data.get('description', 'Funds addition request')
            
            if not amount:
                return JsonResponse({'success': False, 'error': 'Amount is required'})
            
            try:
                amount = float(amount)
                if amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Amount must be positive'})
                if amount > 1000:  # Limit maximum request amount
                    return JsonResponse({'success': False, 'error': 'Maximum request amount is $1000'})
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid amount format'})
            
            # Create funding request
            funding_request = FundingRequest.objects.create(
                user=request.user,
                amount=amount,
                description=description
            )
            
            # Create notification for funding request submission
            from core.models import Notification
            Notification.create_notification(
                user=request.user,
                notification_type='wallet_funded',
                title='Funding Request Submitted',
                message=f'Your funding request for ${amount} has been submitted and is pending admin approval.',
                appointment=None
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Funding request for ${amount} submitted successfully. It will be reviewed by an administrator.',
                'request_id': funding_request.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class PayAppointmentAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to pay for appointment from wallet"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a patient"""
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'})
        
        if request.user.role != 'patient':
            return JsonResponse({'success': False, 'error': 'Only patients can make payments'})
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            appointment_id = data.get('appointment_id')
            
            if not appointment_id:
                return JsonResponse({'success': False, 'error': 'Appointment ID is required'})
            
            appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
            
            # Check if appointment is already paid or confirmed
            if appointment.status == 'confirmed':
                return JsonResponse({'success': False, 'error': 'Appointment is already confirmed'})
            
            # Get doctor fee
            doctor_fee = appointment.doctor.fee
            
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            # Check if wallet has sufficient funds
            if not wallet.has_sufficient_funds(doctor_fee):
                return JsonResponse({
                    'success': False, 
                    'error': f'Insufficient funds. Required: ${doctor_fee}, Available: ${wallet.balance}'
                })
            
            with transaction.atomic():
                # Deduct funds from wallet
                new_balance = wallet.deduct_funds(doctor_fee)
                
                # Create transaction record
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='payment',
                    amount=doctor_fee,
                    description=f'Payment for appointment with Dr. {appointment.doctor.user.get_full_name()}',
                    balance_after=new_balance,
                    appointment=appointment
                )
                
                # Update appointment status to confirmed
                appointment.status = 'confirmed'
                appointment.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ${doctor_fee} successful. Appointment confirmed.',
                'new_balance': float(new_balance),
                'appointment_status': appointment.status
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})