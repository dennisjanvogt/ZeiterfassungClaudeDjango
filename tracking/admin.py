# tracking/admin.py
from django.contrib import admin
from .models import Client, Project, TimeEntry
from django.utils import timezone
from .models import UserProfile


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'created_at')
    search_fields = ('name', 'contact_person', 'email')
    list_filter = ('created_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'hourly_rate',
                    'total_hours', 'is_active', 'created_at')
    list_filter = ('is_active', 'client', 'created_at')
    search_fields = ('name', 'client__name', 'description')


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'start_time', 'end_time',
                    'get_rounded_duration', 'is_billable')
    list_filter = ('is_billable', 'project', 'user', 'start_time')
    search_fields = ('description', 'project__name', 'user__username')

    def get_rounded_duration(self, obj):
        return obj.get_rounded_duration() if obj.duration else "-"
    get_rounded_duration.short_description = "Dauer (gerundet)"


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved', 'approval_date')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'user__email',
                     'user__first_name', 'user__last_name')
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        for profile in queryset:
            if not profile.is_approved:
                profile.is_approved = True
                profile.approval_date = timezone.now()
                profile.save()

        count = queryset.count()
        if count == 1:
            message_bit = "1 Benutzer wurde"
        else:
            message_bit = f"{count} Benutzer wurden"
        self.message_user(request, f"{message_bit} erfolgreich genehmigt.")

    approve_users.short_description = "Ausgewählte Benutzer genehmigen"


admin.site.register(UserProfile, UserProfileAdmin)
