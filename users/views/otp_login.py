from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

from users.forms import PhoneNumberForm
from users.utils import create_otp, send_otp

User = get_user_model()


class OTPLoginView(FormView):
    template_name = "users/otp_login.html"
    form_class = PhoneNumberForm

    def form_valid(self, form):
        user = form.get_user()

        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])

        otp = create_otp(user)
        send_otp(user.phone_number, otp.code)

        # Store phone in session
        self.request.session["phone_number"] = user.phone_number

        return redirect("users:verify_phone")


class RetryOTPLoginView(FormView):
    template_name = "users/otp_login.html"  # reuse same template
    form_class = PhoneNumberForm

    def get_initial(self):
        initial = super().get_initial()
        phone_number = self.request.session.get("phone_number")
        if phone_number:
            initial["phone_number"] = phone_number
        return initial

    def form_valid(self, form):
        user = form.get_user()

        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])

        otp = create_otp(user)
        send_otp(user.phone_number, otp.code)

        # Update phone in session
        self.request.session["phone_number"] = user.phone_number

        return redirect("users:verify_phone")
