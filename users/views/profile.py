from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy

from users.models import User
from users.forms import UserProfileForm


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return self.request.user
    