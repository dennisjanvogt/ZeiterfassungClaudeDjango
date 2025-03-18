# models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

import os
from django.db import models
from django.utils import timezone

def organization_logo_path(instance, filename):
    """
    Generate a unique filename for uploaded organization logos
    """
    # Get the file extension
    ext = filename.split('.')[-1]
    # Create a timestamp-based filename
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    # Construct the new filename
    new_filename = f"organization_logos/{timestamp}_{instance.slug}.{ext}"
    return new_filename

class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, help_text="Wird für die URL verwendet")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(
        upload_to=organization_logo_path, 
        blank=True, 
        null=True, 
        verbose_name="Organisationslogo"
    )
    registration_code = models.CharField(max_length=50, unique=True, help_text="Code zum Registrieren von Benutzern")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisationen"


class Client(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='clients', default='')
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    class Meta:
        unique_together = ['organization', 'name']

    def get_current_month_revenue(self):
        today = timezone.now()
        month_start = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        projects = self.projects.all()
        total_revenue = 0

        for project in projects:
            time_entries = project.time_entries.filter(
                start_time__gte=month_start)
            for entry in time_entries:
                total_revenue += entry.get_billable_amount()

        return total_revenue

    def get_current_month_hours(self):
        today = timezone.now()
        month_start = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        projects = self.projects.all()
        total_hours = 0

        for project in projects:
            time_entries = project.time_entries.filter(
                start_time__gte=month_start)
            for entry in time_entries:
                total_hours += entry.get_rounded_duration()

        return total_hours


class Project(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Stundensatz in Euro")
    total_hours = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Gesamtprojektdauer in Stunden")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.name}"

    def get_used_hours(self):
        """Calculate total hours used for this project, respecting factored hours when available"""
        entries = self.time_entries.all()
        used_hours = 0

        for entry in entries:
            if entry.end_time:  # Only count completed entries
                if entry.factored_hours is not None:
                    # Use factored hours if available
                    used_hours += entry.factored_hours
                else:
                    # Otherwise use rounded duration
                    used_hours += entry.get_rounded_duration()

        return used_hours

    def get_used_hours_by_user(self, user):
        """Gibt die bisher verbrauchten Stunden eines bestimmten Benutzers zurück."""
        from decimal import Decimal

        total = self.time_entries.filter(user=user).aggregate(
            total=Sum('duration'))['total']
        if total is not None:
            return total

    def get_remaining_hours(self):
        """Berechnet die noch verfügbaren Stunden."""
        remaining = self.total_hours - self.get_used_hours()
        return remaining if remaining > 0 else 0

    def get_percentage_used(self):
        """Berechnet den prozentualen Fortschritt des Projekts."""
        from decimal import Decimal

        if self.total_hours <= 0:
            return Decimal('0.0')

        used_hours = self.get_used_hours()

        # Sicherstellung, dass total_hours nicht Null ist
        percentage = (used_hours / self.total_hours) * 100

        # Begrenzung auf 100%
        if percentage > 100:
            return Decimal('100.0')

        return percentage


class TimeEntry(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='time_entries')
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    duration = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Dauer in Stunden")
    is_billable = models.BooleanField(default=True)
    factored_hours = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        verbose_name="Fakturierte Stunden",
        help_text="Optional. Wenn leer, wird die gerundete Dauer verwendet.")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.project.name} - {self.start_time.strftime('%d.%m.%Y')}"

    def save(self, *args, **kwargs):
        if self.end_time and not self.duration:
            duration_seconds = (
                self.end_time - self.start_time).total_seconds()
            self.duration = round(duration_seconds / 3600,
                                  2)  # Convert to hours

        # Set the updated_at timestamp
        self.updated_at = timezone.now()

        # Only set created_at when creating new object
        if not self.pk:
            self.created_at = timezone.now()

        super().save(*args, **kwargs)

    def get_rounded_duration(self):
        """Round duration to nearest quarter hour"""
        if not self.duration:
            return 0

        quarters = round(self.duration * 4) / 4  # Round to nearest 0.25
        return quarters

    def get_billable_amount(self):
        if not self.is_billable:
            return 0

        # Use factored_hours if available, otherwise use rounded duration
        if self.factored_hours is not None:
            hours = self.factored_hours
        else:
            hours = Decimal(str(self.get_rounded_duration()))

        return hours * self.project.hourly_rate

    def is_running(self):
        return self.start_time and not self.end_time


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='user_profiles', default='')
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.organization.name}) - {'Genehmigt' if self.is_approved else 'Ausstehend'}"

    class Meta:
        verbose_name = "Benutzerprofil"
        verbose_name_plural = "Benutzerprofile"
        unique_together = ['user', 'organization']  # Ein Benutzer kann nur ein Profil pro Organisation haben



@receiver(post_save, sender=UserProfile)
def notify_user_approved(sender, instance, **kwargs):
    """Benachrichtigt den Benutzer, wenn sein Profil genehmigt wurde."""
    if instance.is_approved and instance.approval_date:
        # Hier könnte man eine E-Mail-Benachrichtigung senden
        # Beispiel:
        # send_mail(
        #     'Dein Konto wurde freigeschaltet',
        #     f'Hallo {instance.user.username},\n\nDein Konto wurde von einem Administrator freigeschaltet. Du kannst dich jetzt anmelden.',
        #     'from@example.com',
        #     [instance.user.email],
        #     fail_silently=False,
        # )
        pass
