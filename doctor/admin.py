from django.contrib import admin
from .models import Doctor, Timeslot


class TimeslotInline(admin.TabularInline):
    model = Timeslot
    extra = 1
    fields = ('start_time', 'end_time', 'is_booked')
    readonly_fields = ('is_booked',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'specialty', 'fee', 'availability', 'average_rating')
    list_filter = ('specialty', 'availability')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty')
    inlines = [TimeslotInline]


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked',)
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')
