from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UserLoginView, 
    UserSignUpView, 
    UpdateProfileView,
    UserPasswordResetCompleteView,
    UserPasswordResetConfirmView,
    UserPasswordResetDoneView,
    UserPasswordResetView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView
)


urlpatterns = [
    path("signup/", UserSignUpView.as_view(), name="signup"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('profile/', UpdateProfileView.as_view(), name='profile'),

    path("password-change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", UserPasswordChangeDoneView.as_view(), name="password_change_done"),

    path("password-reset/", UserPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", UserPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", UserPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
