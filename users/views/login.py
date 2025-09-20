from django.contrib.auth.views import LoginView

from users.forms import UserAuthenticationForm


class UserLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = UserAuthenticationForm