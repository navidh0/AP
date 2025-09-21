from django.views.generic import FormView
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model

from users.forms import OTPCodeForm
from users.utils import verify_otp

User = get_user_model()


class VerifyPhoneView(FormView):
    template_name = "users/verify_phone.html"
    form_class = OTPCodeForm

    def form_valid(self, form):
        phone_number = self.request.session.get("phone_number")
        if not phone_number:
            return redirect("users:otp_login")

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return render(self.request, self.template_name, {
                "form": form,
                "error": "Session expired. Please try again."
            })

        code = form.cleaned_data["otp_code"]
        if verify_otp(user, code):
            login(self.request, user)
            self.request.session.pop("phone_number", None)
            return redirect('home')

        return render(self.request, self.template_name, {
            "form": form,
            "error": "Invalid or expired code."
        })
