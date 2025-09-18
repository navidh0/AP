from django.contrib.auth.forms import UserCreationForm
from django import forms

from .mixins import TailwindFormMixin
from users.models import User


class UserSignUpForm(TailwindFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "username", "email",
            "phone_number", "ssn", "birth_date", "gender",
            "role", "avatar", "password1", "password2",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}), # HTML date picker
            "avatar": forms.FileInput(attrs={"accept": "image/png, image/jpeg"}),
        }
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "username": "Username",
            "email": "Email",
            "phone_number": "Phone number",
            "ssn": "SSN",
            "birth_date": "Birth date",
            "gender": "Gender",
            "role": "Role",
            "avatar": "Avatar",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom help texts only for this form
        self.fields["username"].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        self.fields["password1"].help_text = (
            "<ul class='list-disc list-inside text-xs text-neutral-500 mt-1'>"
            "<li>Must be at least 8 characters long</li>"
            "<li>Cannot be too common</li>"
            "<li>Cannot be entirely numeric</li>"
            "</ul>"
        )
        self.fields["password2"].help_text = "Enter the same password as above"

        # Removing the auto focus from username
        self.fields["username"].widget.attrs.update({"autofocus": False})
