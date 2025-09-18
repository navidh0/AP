from django.contrib.auth.views import (
    PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy

from users.forms import UserPasswordChangeForm


class UserPasswordChangeView(PasswordChangeView):
    template_name = "users/password_change.html"
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "users/password_change_done.html"