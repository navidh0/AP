from django.contrib import admin
from .models import Doctor, Timeslot, Comment

class TimeslotInline(admin.TabularInline):
    model = Timeslot
    extra = 1
    fields = ('start_time', 'end_time', 'is_booked')
    readonly_fields = ('is_booked',)



@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty','fee', 'availability', 'average_rating')
    list_filter = ('specialty', 'availability')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty')
    inlines = [TimeslotInline]


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked',)
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')






#Register doctor comment write by user in the admin site 
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "get_patient_name",
        "get_doctor_name",
        "title",
        "doctor_rating",
         "created_at",
         )
    list_filter = ("doctor_rating","is_anonymous", "doctor__specialty")
    search_fields = (
        'title',
        'user__username',
        'user__first_name',
        'user__last_name',
        'doctor__user__username',
        'doctor__user__first_name',
        'doctor__user__last_name',
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ('-created_at',)
    list_per_page = 25



    def get_patient_name(self, obj):
         """Show patient name or Anonymous"""
         if obj.is_anonymous:
            return "Anonymous"
         return obj.user.get_full_name() or obj.user.username
    get_patient_name.short_description = "Patient"

    def get_doctor_name(self, obj):
         """Show doctor name"""
         return f"Dr.{obj.doctor.user.get_full_name() or obj.doctor.user.username}"
    get_doctor_name.short_description = "Doctor"