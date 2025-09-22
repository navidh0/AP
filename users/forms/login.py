from django.contrib.auth.forms import AuthenticationForm
from django import forms

from .mixins import TailwindFormMixin


class UserAuthenticationForm(TailwindFormMixin, AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your password",
        })
    )
