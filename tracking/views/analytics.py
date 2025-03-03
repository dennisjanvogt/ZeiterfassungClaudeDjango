from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from tracking.models import Client, TimeEntry
from django.contrib.auth.models import User
from datetime import datetime
from decimal import Decimal


@login_required
def analytics(request):
    clients = Client.objects.all()
    users = User.objects.all()  # Alle Benutzer für den Filter abrufen
    
    # Default to current month
    today = timezone.now().date()
    start_date = today.replace(day=1)

    # Handle date range selection
    if 'start_date' in request.GET and request.GET['start_date']:
        try:
            start_date = datetime.strptime(
                request.GET['start_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    end_date = today
    if 'end_date' in request.GET and request.GET['end_date']:
        try:
            end_date = datetime.strptime(
                request.GET['end_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    # Filter by client
    client_id = request.GET.get('client_id')

    # Filter by user (neu)
    user_id = request.GET.get('user_id')

    # Erstelle die Basisabfrage
    entries = TimeEntry.objects.filter(
        start_time__date__gte=start_date,
        start_time__date__lte=end_date
    )

    # Anwenden des Client-Filters, wenn vorhanden
    if client_id:
        entries = entries.filter(project__client_id=client_id)

    # Anwenden des User-Filters, wenn vorhanden
    if user_id:
        entries = entries.filter(user_id=user_id)

    # Calculate metrics
    total_hours = sum(entry.get_rounded_duration() for entry in entries)
    total_revenue = sum(entry.get_billable_amount() for entry in entries)

    # Berechne durchschnittliche Stunden pro Tag und Umsatz pro Stunde
    avg_hours_per_day = 0
    avg_revenue_per_hour = 0

    days_diff = (end_date - start_date).days + 1
    if days_diff > 0 and total_hours > 0:
        avg_hours_per_day = total_hours / days_diff

    if total_hours > 0:
        # Convert float to Decimal before division
        total_hours_decimal = Decimal(str(total_hours))
        avg_revenue_per_hour = total_revenue / total_hours_decimal

    # Group by client
    client_data = {}
    for entry in entries:
        client = entry.project.client
        if client.id not in client_data:
            client_data[client.id] = {
                'client': client,
                'hours': 0,
                'revenue': 0,
                'projects': {}
            }

        client_data[client.id]['hours'] += entry.get_rounded_duration()
        client_data[client.id]['revenue'] += entry.get_billable_amount()

        project = entry.project
        if project.id not in client_data[client.id]['projects']:
            client_data[client.id]['projects'][project.id] = {
                'project': project,
                'hours': 0,
                'revenue': 0
            }

        client_data[client.id]['projects'][project.id]['hours'] += entry.get_rounded_duration()
        client_data[client.id]['projects'][project.id]['revenue'] += entry.get_billable_amount()

    context = {
        'clients': clients,
        'users': users,  # Alle Benutzer für den Filter bereitstellen
        'start_date': start_date,
        'end_date': end_date,
        'selected_client_id': client_id,
        'selected_user_id': user_id,  # Ausgewählten Benutzer im Kontext speichern
        'total_hours': total_hours,
        'total_revenue': total_revenue,
        'client_data': client_data.values(),
        'avg_hours_per_day': avg_hours_per_day,
        'avg_revenue_per_hour': avg_revenue_per_hour,
    }

    return render(request, 'tracking/analytics.html', context)
