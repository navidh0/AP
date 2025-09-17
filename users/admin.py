# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # This is the layout for the "Change user" page
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role", "phone_number", "ssn", "birth_date", "gender")}),
    )

    # This is the layout for the "Add user" page
    add_fieldsets = UserAdmin.add_fieldsets + (
        # Add a new section for personal info
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        # Add your custom fields
        ("Additional Info", {"fields": ("role", "phone_number", "ssn", "birth_date", "gender")}),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
    )