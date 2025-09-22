from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'timeslot', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'doctor__specialty']
    search_fields = ['patient__username', 'patient__first_name', 'patient__last_name', 'doctor__user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('patient', 'doctor', 'timeslot', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'doctor__user', 'timeslot')
