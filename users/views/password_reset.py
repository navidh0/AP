from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.urls import reverse_lazy

from users.forms import UserPasswordResetForm, UserSetPasswordForm


class UserPasswordResetView(PasswordResetView):
    template_name = "users/password_reset.html"         
    form_class = UserPasswordResetForm
    subject_template_name = "users/emails/password_reset_subject.txt" 
    email_template_name = "users/emails/password_reset_email.txt"     
    success_url = reverse_lazy("users:password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("users:password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"

