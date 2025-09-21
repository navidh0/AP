from django.views import View
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

from users.utils import create_otp, send_otp

User = get_user_model()


class ResendOTPView(View):
    def get(self, request, *args, **kwargs):
        phone_number = request.session.get("phone_number")
        if not phone_number:
            return redirect("users:otp_login")

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return redirect("users:otp_login")

        # Create and send new OTP
        otp = create_otp(user)
        send_otp(user.phone_number, otp.code)

        # Just redirect back to verify without messages
        return redirect("users:verify_phone")
