# tracking/admin.py
from django.contrib import admin
from .models import Client, Organization, Project, TimeEntry
from django.utils import timezone
from .models import UserProfile
from django.db import models

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'registration_code', 'contact_email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}  # Automatisches Ausfüllen des Slugs basierend auf dem Namen
    
    # Unterstütze Datei-Upload für Logos
    formfield_overrides = {
        models.ImageField: {'widget': admin.widgets.AdminFileWidget},
    }

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'contact_person', 'email', 'phone', 'created_at')
    search_fields = ('name', 'contact_person', 'email', 'organization__name')
    list_filter = ('organization', 'created_at')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'client_organization', 'hourly_rate',
                    'total_hours', 'is_active', 'created_at')
    list_filter = ('is_active', 'client__organization', 'created_at')
    search_fields = ('name', 'client__name', 'description', 'client__organization__name')
    
    def client_organization(self, obj):
        return obj.client.organization
    client_organization.short_description = "Organisation"
    client_organization.admin_order_field = "client__organization__name"


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'project_organization', 'start_time', 'end_time',
                    'get_rounded_duration', 'is_billable')
    list_filter = ('is_billable', 'project__client__organization', 'user', 'start_time')
    search_fields = ('description', 'project__name', 'user__username', 'project__client__organization__name')

    def get_rounded_duration(self, obj):
        return obj.get_rounded_duration() if obj.duration else "-"
    get_rounded_duration.short_description = "Dauer (gerundet)"
    
    def project_organization(self, obj):
        return obj.project.client.organization
    project_organization.short_description = "Organisation"
    project_organization.admin_order_field = "project__client__organization__name"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'is_approved', 'approval_date')
    list_filter = ('is_approved', 'organization')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'organization__name')
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

