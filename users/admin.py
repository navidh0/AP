from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra Info", {
            "fields": ("avatar", "role", "phone_number", "ssn", "birth_date", "gender"),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {
            "fields": ("avatar", "role", "phone_number", "ssn", "birth_date", "gender"),
        }),
    )
    list_display = ("username", "email", "role", "phone_number", "ssn", "is_staff")
    search_fields = ("username", "email", "phone_number", "ssn")
    list_filter = ("role", "gender", "is_staff", "is_superuser")
