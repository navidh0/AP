from django import forms

from .mixins import TailwindFormMixin
from users.models import User


class UserProfileForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "username", "email",
            "phone_number", "ssn", "birth_date", "gender",
            "role", "avatar",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}), 
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
        # Profile-specific customizations
        self.fields["username"].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
