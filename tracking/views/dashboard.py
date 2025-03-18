# tracking/views/dashboard.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tracking.models import Project, TimeEntry


@login_required
def dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Aktuelle Organisation aus dem Request
    current_organization = getattr(request, 'organization', None)
    
    if not current_organization:
        return render(request, 'tracking/dashboard.html', {
            'today_hours': 0,
            'today_revenue': 0,
            'month_hours': 0,
            'month_revenue': 0,
            'active_timer': None,
            'recent_entries': [],
            'projects_warning': [],
            'no_organization': True  # Flag für fehlende Organisation
        })

    # Today's stats - nur eigene Einträge der aktuellen Organisation
    today_entries = TimeEntry.objects.filter(
        user=request.user,
        start_time__date=today,
        project__client__organization=current_organization
    )
    today_hours = sum(entry.get_rounded_duration() for entry in today_entries)
    today_revenue = sum(entry.get_billable_amount() for entry in today_entries)

    # Month's stats - nur eigene Einträge der aktuellen Organisation
    month_entries = TimeEntry.objects.filter(
        user=request.user,
        start_time__date__gte=month_start,
        start_time__date__lte=today,
        project__client__organization=current_organization
    )
    month_hours = sum(entry.get_rounded_duration() for entry in month_entries)
    month_revenue = sum(entry.get_billable_amount() for entry in month_entries)

    # Active timer - nur eigener Timer der aktuellen Organisation
    active_timer = TimeEntry.objects.filter(
        user=request.user, 
        end_time__isnull=True,
        project__client__organization=current_organization
    ).first()

    # Recent entries - nur eigene Einträge der aktuellen Organisation
    recent_entries = TimeEntry.objects.filter(
        user=request.user,
        project__client__organization=current_organization
    ).order_by('-start_time')[:5]

    # Projects nearing their total hours limit - Alle Projekte der aktuellen Organisation
    projects = Project.objects.filter(
        is_active=True,
        client__organization=current_organization
    )
    projects_warning = []

    for project in projects:
        # Berechne den prozentualen Fortschritt
        used_hours = project.get_used_hours()
        if project.total_hours > 0:
            percentage_used = (used_hours / project.total_hours) * 100
        else:
            percentage_used = 0

        # Stelle sicher, dass der Prozentsatz nicht größer als 100 ist
        if percentage_used > 100:
            percentage_used = 100

        # Füge Projekte mit hoher Auslastung hinzu
        if percentage_used > 80:
            projects_warning.append({
                'project': project,
                'percentage_used': percentage_used,
                'remaining_hours': project.get_remaining_hours()
            })

    return render(request, 'tracking/dashboard.html', {
        'today_hours': today_hours,
        'today_revenue': today_revenue,
        'month_hours': month_hours,
        'month_revenue': month_revenue,
        'active_timer': active_timer,
        'recent_entries': recent_entries,
        'projects_warning': projects_warning,
    })