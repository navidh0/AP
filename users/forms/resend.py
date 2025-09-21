from django import forms
from users.forms.mixins import TailwindFormMixin


class ResendActivationForm(TailwindFormMixin, forms.Form):
    email = forms.EmailField(label="Email")
