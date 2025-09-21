from django.views.generic import FormView
from django.shortcuts import redirect
from django.urls import reverse
from django.core import signing
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile

from users.forms import UserSignUpForm
from users.utils import send_activation_email


def _sanitize_user_data(cleaned_data):
    """
    Store only serializable fields in user_data.
    If there's a file, save it using Django storage and
    store only the file path.
    """
    safe_data = {}
    for key, value in cleaned_data.items():
        if isinstance(value, UploadedFile):
            # Save file into MEDIA_ROOT/pending/
            file_path = default_storage.save(f"pending/{value.name}", value)
            safe_data[f"{key}_path"] = file_path
        else:
            safe_data[key] = value
    return safe_data


class UserSignUpView(FormView):
    template_name = "users/signup.html"
    form_class = UserSignUpForm

    def form_valid(self, form):
        user_data = _sanitize_user_data(form.cleaned_data)

        # Save user_data in session (JSON-safe)
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
        user_data = _sanitize_user_data(form.cleaned_data)

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
