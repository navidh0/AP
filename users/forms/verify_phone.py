from django import forms
from .mixins import TailwindFormMixin 


class OTPCodeForm(TailwindFormMixin, forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        label="Enter OTP",
        widget=forms.TextInput(attrs={"placeholder": "6-digit code"})
    )
