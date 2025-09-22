from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.urls import reverse_lazy


class UserLogoutView(View):
    """Custom logout view that accepts GET requests"""
    
    def get(self, request):
        """Handle GET request for logout"""
        logout(request)
        return redirect(reverse_lazy('users:login'))
    
    def post(self, request):
        """Handle POST request for logout (for forms)"""
        logout(request)
        return redirect(reverse_lazy('users:login'))
