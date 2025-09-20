from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django import forms

from .mixins import TailwindFormMixin
from users.models import User


class UserPasswordResetForm(TailwindFormMixin, PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your email",
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email does not match any account.")
        return email


class UserSetPasswordForm(TailwindFormMixin, SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "New password",
        }),
        help_text=(
            "<ul class='list-disc list-inside text-xs text-neutral-500 mt-1'>"
            "<li>Must be at least 8 characters long</li>"
            "<li>Cannot be too common</li>"
            "<li>Cannot be entirely numeric</li>"
            "</ul>"
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm new password",
        })
    )
