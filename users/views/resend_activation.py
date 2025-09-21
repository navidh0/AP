from django.views import View
from django.shortcuts import redirect
from django.urls import reverse
from django.core import signing

from users.utils import send_activation_email


class ResendActivationView(View):
    def get(self, request):
        # Retrieve stored user_data from session
        user_data = request.session.get("pending_user_data")

        if not user_data:
            # No pending signup → redirect to signup
            return redirect("users:signup")

        # Create fresh token (new 5-minute expiry)
        token = signing.dumps(user_data, salt="user-activation")
        link = request.build_absolute_uri(
            reverse("users:activate", kwargs={"token": token})
        )

        # Resend activation email
        send_activation_email(request, user_data, link)

        return redirect("users:activation_sent")
