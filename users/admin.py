from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_email_verified', 'is_phone_verified')
    list_filter = ('role', 'is_active', 'is_email_verified', 'is_phone_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'ssn', 'avatar', 'birth_date', 'gender', 'is_phone_verified', 'is_email_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'ssn', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'expire_date', 'created_at', 'is_valid')
    list_filter = ('created_at', 'expire_date')
    search_fields = ('user__username', 'user__phone_number', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
