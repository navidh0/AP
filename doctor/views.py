from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.utils import timezone
from datetime import timedelta, date
from .models import Doctor, Timeslot, User, Comment, DoctorAvailability
from .forms import CommentForm
from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse


class DoctorListView(ListView):
    """View to display a list of all doctors."""
    model = Doctor
    template_name = 'doctor/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 10

    from django.utils import timezone
    from datetime import timedelta

    def get_queryset(self):
        """
        Overrides the default queryset to filter based on GET parameters.
        """
        from django.db.models import Q
        
        queryset = Doctor.objects.all()

        # Get filter parameters from the URL
        search = self.request.GET.get('search')
        specialty = self.request.GET.get('specialty')
        gender = self.request.GET.get('gender')
        availability = self.request.GET.get('availability')
        vacant_for = self.request.GET.get('vacant_for')

        # Search functionality
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specialty__icontains=search) |
                Q(user__email__icontains=search)
            )

        if specialty:
            queryset = queryset.filter(specialty__iexact=specialty)

        if gender:
            queryset = queryset.filter(user__gender=gender)

        if availability:
            queryset = queryset.filter(availability=True)

        if vacant_for:
            today = timezone.localdate()
            now = timezone.localtime()
            tomorrow = today + timedelta(days=1)

            if vacant_for == 'today':
                doctor_ids = Timeslot.objects.filter(
                    is_booked=False,
                    end_time__gte=today,
                    start_time__lte=today,
                ).values_list('doctor_id', flat=True).distinct()

            elif vacant_for == 'tomorrow':
                doctor_ids = Timeslot.objects.filter(
                    is_booked=False,
                    start_time__date__lte=tomorrow,
                    end_time__date__gte=tomorrow,
                ).values_list('doctor_id', flat=True).distinct()

            else:
                doctor_ids = None

            if doctor_ids:
                queryset = queryset.filter(pk__in=doctor_ids)

        return queryset.order_by('user__first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current filter values for template
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'specialty': self.request.GET.get('specialty', ''),
            'gender': self.request.GET.get('gender', ''),
            'availability': self.request.GET.get('availability', ''),
            'vacant_for': self.request.GET.get('vacant_for', ''),
        }
        
        # Get unique specialties for filter dropdown
        context['specialties'] = Doctor.objects.values_list('specialty', flat=True).distinct().order_by('specialty')
        
        return context
    

class DoctorDetailView(DetailView):
    """View to display the details of a single doctor."""
    model = Doctor
    template_name = 'doctor/doctor_detail.html'
    context_object_name = 'doctor'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        doctor = self.get_object()

        #get all comment for this doctor 
        comments = Comment.objects.filter(doctor=doctor).order_by('-created_at')

        #check the current user already commented
        user_has_commented = False
        if self.request.user.is_authenticated:
            user_has_commented = Comment.objects.filter(
                doctor=doctor,
                user = self.request.user
            ).exists()
        
        # Get available timeslots for the next 30 days
        from datetime import timedelta
        start_date = timezone.now()
        end_date = start_date + timedelta(days=30)
        
        available_slots = Timeslot.objects.filter(
            doctor=doctor,
            is_booked=False,
            start_time__gte=start_date,
            start_time__lte=end_date
        ).order_by('start_time')
        
        context.update({
            'comments': comments,
            'comment_form': CommentForm(),
            'user_has_commented': user_has_commented,
            'total_comments': comments.count(),
            'available_slots': available_slots,
            'has_available_slots': available_slots.exists(),
        })

        return context


class DoctorCreateView(CreateView):
    """View to add a new doctor via a form."""
    model = Doctor
    template_name = 'doctor/doctor_form.html'
    fields = ['user', 'specialty', 'fee', 'availability']
    success_url = reverse_lazy('doctor:doctor-list')  # Redirect to the doctor list on success

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit the 'user' field to only show users with the 'doctor' role
        # form.fields['user'].queryset = User.objects.filter(role='doctor')
        form.fields['user'].queryset = User.objects.all()
        return form


class TimeslotCreateView(CreateView):
    """View to add a new timeslot for a specific doctor."""
    model = Timeslot
    template_name = 'doctor/timeslot_form.html'
    fields = ['start_time', 'end_time']

    def form_valid(self, form):
        # Automatically associate the timeslot with the correct doctor from the URL
        doctor = get_object_or_404(Doctor, pk=self.kwargs['doctor_id'])
        form.instance.doctor = doctor
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to the doctor's detail page after adding a timeslot
        return reverse_lazy('doctor:doctor-detail', kwargs={'pk': self.kwargs['doctor_id']})




class CommentCreateView(LoginRequiredMixin, CreateView):
    """ view to create a new comment for the doctor  """
    model = Comment
    form_class = CommentForm
    template_name = 'doctor/comment_form.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        doctor = get_object_or_404(Doctor, pk=self.kwargs['doctor_id'])
        context['doctor'] = doctor
        return context

    def dispatch(self, request, *args, **kwargs):
        # check if user is a patient 
        if not request.user.is_authenticated or request.user.role != 'patient' :
            messages.error(request, 'Only patients can leave reviews.')
            return redirect('doctor:doctor-detail', pk=self.kwargs['doctor_id'])
        return super().dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        doctor = get_object_or_404(Doctor, pk=self.kwargs['doctor_id'])

        #check the user already has comment on this doctor 
        existing_comment = Comment.objects.filter(
            doctor=doctor,
            user=self.request.user
        ).first()

        if existing_comment:
            messages.error(self.request, 'You have already reviewed this doctor.')
            return redirect('doctor:doctor-detail', pk=doctor.pk)
        form.instance.doctor = doctor
        form.instance.user = self.request.user

        messages.success(self.request, 'Your review has been submitted successfully.')
        return super().form_valid(form)



    def get_success_url(self):
        return reverse_lazy('doctor:doctor-detail', kwargs={'pk': self.kwargs['doctor_id']})


# -----------------------------
# Availability Management Views
# -----------------------------

class DoctorAvailabilityCreateView(LoginRequiredMixin, CreateView):
    """View for doctors to create their availability windows"""
    model = DoctorAvailability
    template_name = 'doctor/availability_form.html'
    fields = ['day_of_week', 'start_time', 'end_time', 'visit_duration', 'is_active']
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a doctor
        if not request.user.is_authenticated or request.user.role != 'doctor':
            messages.error(request, 'Only doctors can manage availability.')
            return redirect('doctor:doctor-list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Get the doctor profile for the current user
        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            messages.error(self.request, 'Doctor profile not found.')
            return redirect('doctor:doctor-list')
        
        form.instance.doctor = doctor
        response = super().form_valid(form)
        
        # Automatically generate timeslots for the next 30 days
        if form.instance.is_active:
            from datetime import date, timedelta
            start_date = date.today()
            end_date = start_date + timedelta(days=30)
            
            try:
                generated_timeslots = Timeslot.generate_for_doctor(doctor, start_date, end_date)
                messages.success(self.request, f'Availability window added successfully. Generated {len(generated_timeslots)} timeslots for the next 30 days.')
            except Exception as e:
                messages.warning(self.request, f'Availability window added, but there was an issue generating timeslots: {str(e)}')
        else:
            messages.success(self.request, 'Availability window added successfully.')
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('doctor:doctor-detail', kwargs={'pk': self.request.user.doctor_profile.pk})


class TimeslotListView(TemplateView):
    """View to display timeslots for a doctor grouped by days"""
    template_name = 'doctor/timeslot_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = get_object_or_404(Doctor, pk=self.kwargs['doctor_id'])
        
        # Get date filter from URL parameters
        date_filter = self.request.GET.get('date')
        timeslots_by_date = {}
        
        if date_filter:
            try:
                from datetime import date
                target_date = date.fromisoformat(date_filter)
                timeslots = Timeslot.objects.filter(
                    doctor=doctor,
                    start_time__date=target_date
                ).order_by('start_time')
                
                # Group by date (single date)
                timeslots_by_date = {target_date: timeslots}
            except ValueError:
                timeslots_by_date = {}
        else:
            # Default: show timeslots for the next 30 days (both available and unavailable)
            today = timezone.now().date()
            future_date = today + timedelta(days=30)
            
            timeslots = Timeslot.objects.filter(
                doctor=doctor,
                start_time__date__gte=today,
                start_time__date__lte=future_date
            ).order_by('start_time')
            
            # Group timeslots by date
            for timeslot in timeslots:
                slot_date = timeslot.start_time.date()
                if slot_date not in timeslots_by_date:
                    timeslots_by_date[slot_date] = []
                timeslots_by_date[slot_date].append(timeslot)
        
        # Sort dates
        sorted_dates = sorted(timeslots_by_date.keys())
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(sorted_dates, 7)  # Show 7 days per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get timeslots for the current page dates with counts
        current_page_timeslots = {}
        for date in page_obj.object_list:
            day_timeslots = timeslots_by_date[date]
            available_count = sum(1 for ts in day_timeslots if not ts.is_booked)
            booked_count = sum(1 for ts in day_timeslots if ts.is_booked)
            
            current_page_timeslots[date] = {
                'timeslots': day_timeslots,
                'available_count': available_count,
                'booked_count': booked_count,
                'total_count': len(day_timeslots)
            }
        
        context.update({
            'doctor': doctor,
            'timeslots_by_date': current_page_timeslots,
            'page_obj': page_obj,
            'selected_date': date_filter or '',
        })
        return context


class GenerateTimeslotsAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to generate timeslots for a doctor within a date range"""
    
    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        
        # Check if user is the doctor or an admin
        if request.user.role not in ['doctor', 'admin'] or (request.user.role == 'doctor' and doctor.user != request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            
            if not start_date_str or not end_date_str:
                return JsonResponse({'error': 'Start date and end date are required'}, status=400)
            
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            
            # Generate timeslots
            generated_timeslots = Timeslot.generate_for_doctor(doctor, start_date, end_date)
            
            return JsonResponse({
                'success': True,
                'message': f'Generated {len(generated_timeslots)} timeslots',
                'count': len(generated_timeslots)
            })
            
        except ValueError as e:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)