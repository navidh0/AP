from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView

from django.utils import timezone
from datetime import timedelta

from .models import Doctor, Timeslot, User


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
