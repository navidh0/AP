from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.urls import path
from .views import (
    UserLoginView, 
    UserSignUpView, 
    RetrySignUpView,
    ActivateView, 
    ResendActivationView, 
    OTPLoginView,
    RetryOTPLoginView,
    ResendOTPView,
    VerifyPhoneView,
    UpdateProfileView,
    UserPasswordResetCompleteView,
    UserPasswordResetConfirmView,
    UserPasswordResetDoneView,
    UserPasswordResetView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView
)


urlpatterns = [
    # --- Sign up / Activation ---
    path("signup/", UserSignUpView.as_view(), name="signup"),
    path("retry-signup/", RetrySignUpView.as_view(), name="retry_signup"),
    path(
        "activation-sent/",
        TemplateView.as_view(template_name="users/activation_sent.html"),
        name="activation_sent",
    ),
    path("activate/<str:token>/", ActivateView.as_view(), name="activate"),
    path("resend-activation/", ResendActivationView.as_view(), name="resend_activation"),

    # --- Authentication ---
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("otp-login/", OTPLoginView.as_view(), name="otp_login"),
    path("retry-otp-login/", RetryOTPLoginView.as_view(), name="retry_otp_login"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),
    path("verify-phone/", VerifyPhoneView.as_view(), name="verify_phone"),

    # --- Profile ---
    path("profile/", UpdateProfileView.as_view(), name="profile"),

    # --- Password change ---
    path("password-change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", UserPasswordChangeDoneView.as_view(), name="password_change_done"),

    # --- Password reset ---
    path("password-reset/", UserPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", UserPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", UserPasswordResetCompleteView.as_view(), name="password_reset_complete"),

]