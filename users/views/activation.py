from django.views import View
from django.shortcuts import render
from django.core import signing
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import File

User = get_user_model()


class ActivateView(View):
    def get(self, request, token):
        try:
            # Token expires in 5 minutes (300 seconds)
            user_data = signing.loads(token, salt="user-activation", max_age=300)
        except signing.SignatureExpired:
            return render(request, "users/activation_invalid.html", {
                "error_title": "Activation Link Expired",
                "error_message": (
                    "Your activation link has expired. "
                    "For security, links are valid for only 5 minutes. "
                    "Please request a new one below."
                ),
                "show_resend": True,
            })
        except signing.BadSignature:
            return render(request, "users/activation_invalid.html", {
                "error_title": "Invalid Activation Link",
                "error_message": (
                    "The activation link is invalid or has been tampered with. "
                    "Please request a new one below."
                ),
                "show_resend": True,
            })

        # ✅ Extract avatar path directly from token data
        file_path = user_data.pop("avatar_path", None)

        # ✅ Create and save the user
        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone_number=user_data["phone_number"],
            ssn=user_data["ssn"],
            role=user_data["role"],
            birth_date=user_data.get("birth_date"),
            gender=user_data.get("gender"),
            is_active=True,
            is_email_verified=True,
        )
        user.set_password(user_data["password1"])  # hash password

        # ✅ Handle avatar safely with a context manager
        if file_path and default_storage.exists(file_path):
            with default_storage.open(file_path, "rb") as f:
                user.avatar.save(
                    file_path.split("/")[-1],  # filename
                    File(f),
                    save=True
                )
            # Delete after file is closed → no Windows lock issue
            default_storage.delete(file_path)

        user.save()

        # ✅ Session cleanup (if any retry data exists)
        request.session.pop("pending_user_data", None)

        return render(request, "users/activation_success.html")
