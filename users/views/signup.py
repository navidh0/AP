from django.views.generic import FormView
from django.contrib.auth import login
from django.urls import reverse_lazy

from users.forms import UserSignUpForm


class UserSignUpView(FormView):
    template_name = "users/signup.html"   
    form_class = UserSignUpForm
    success_url = reverse_lazy("home")  # redirect after signup

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)  # automatically log in user after signup
        return super().form_valid(form)
    