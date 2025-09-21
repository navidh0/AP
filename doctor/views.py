from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.utils import timezone
from datetime import timedelta
from .models import Doctor, Timeslot, User, Comment
from .forms  import CommentForm
from django.db.models  import Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


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
        queryset = Doctor.objects.all()

        # Get filter parameters from the URL
        specialty = self.request.GET.get('specialty')
        gender = self.request.GET.get('gender')
        availability = self.request.GET.get('availability')
        vacant_for = self.request.GET.get('vacant_for')

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
        
        context.update({
            'comments': comments,
            'comment_form': CommentForm(),
            'user_has_commented': user_has_commented,
            'total_comments': comments.count(),
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