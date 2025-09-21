from django.views.generic import FormView
from django.shortcuts import redirect
from django.urls import reverse
from django.core import signing

from users.forms import UserSignUpForm
from users.utils import send_activation_email


class UserSignUpView(FormView):
    template_name = "users/signup.html"
    form_class = UserSignUpForm

    def form_valid(self, form):
        user_data = form.cleaned_data

        # Save user_data in session
        self.request.session["pending_user_data"] = user_data

        # Create signed token (5 min expiry)
        token = signing.dumps(user_data, salt="user-activation")
        link = self.request.build_absolute_uri(
            reverse("users:activate", kwargs={"token": token})
        )

        # Send activation email
        send_activation_email(self.request, user_data, link)

        return redirect("users:activation_sent")


class RetrySignUpView(FormView):
    template_name = "users/signup.html"
    form_class = UserSignUpForm

    def get_initial(self):
        # Prefill form with session data if available
        return self.request.session.get("pending_user_data", {})

    def form_valid(self, form):
        user_data = form.cleaned_data

        # Update session with new/edited data
        self.request.session["pending_user_data"] = user_data

        # Create signed token (fresh 5 min expiry)
        token = signing.dumps(user_data, salt="user-activation")
        link = self.request.build_absolute_uri(
            reverse("users:activate", kwargs={"token": token})
        )

        # Send new activation email
        send_activation_email(self.request, user_data, link)

        return redirect("users:activation_sent")
