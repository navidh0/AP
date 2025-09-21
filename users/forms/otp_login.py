from django import forms
from django.contrib.auth import get_user_model
from .mixins import TailwindFormMixin 

User = get_user_model()


class PhoneNumberForm(TailwindFormMixin, forms.Form):
    phone_number = forms.RegexField(
        label="Phone Number",
        max_length=13,
        regex=r'^(\+98|0)\d{10}$',
        error_messages={
            "invalid": "Enter a valid phone number (digits only).",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            raise forms.ValidationError("This phone number does not exist.")
        self._user = user
        return phone

    def get_user(self):
        return self._user
