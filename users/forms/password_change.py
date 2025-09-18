from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .mixins import TailwindFormMixin


class UserPasswordChangeForm(TailwindFormMixin, PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Current password",
        })
    )
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
