from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from tracking.models import Client, Project, TimeEntry
from tracking.forms import ClientForm


@login_required
def client_list(request):
    clients = Client.objects.all().order_by('name')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()

    return render(request, 'tracking/client_list.html', {
        'clients': clients,
        'form': form
    })


@login_required
def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    projects = client.projects.all()

    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Month's stats for this client
    month_entries = TimeEntry.objects.filter(
        project__client=client,
        start_time__date__gte=month_start,
        start_time__date__lte=today
    )
    month_hours = sum(entry.get_rounded_duration() for entry in month_entries)
    month_revenue = sum(entry.get_billable_amount() for entry in month_entries)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)

    return render(request, 'tracking/client_detail.html', {
        'client': client,
        'projects': projects,
        'form': form,
        'month_hours': month_hours,
        'month_revenue': month_revenue,
    })


@login_required
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Prüfen, ob der Benutzer berechtigt ist (optional)
    if not request.user.is_staff:
        messages.error(
            request, "Sie haben keine Berechtigung, Kunden zu löschen.")
        return redirect('client_list')

    if request.method == 'POST':
        # Prüfen, ob noch Projekte existieren
        projects_count = Project.objects.filter(client=client).count()

        if projects_count > 0:
            messages.error(
                request,
                f'Der Kunde "{client.name}" kann nicht gelöscht werden, da er noch {projects_count} Projekte enthält. '
                f'Bitte löschen Sie zuerst alle zugehörigen Projekte.'
            )
            return redirect('client_detail', client_id=client.id)

        # Speichere Kundenname für Erfolgsbenachrichtigung
        client_name = client.name

        # Lösche den Kunden
        client.delete()

        messages.success(
            request, f'Kunde "{client_name}" wurde erfolgreich gelöscht.')
        return redirect('client_list')

    return render(request, 'tracking/confirm_delete.html', {
        'object': client,
        'object_name': f'Kunde "{client.name}"',
        'back_url': request.META.get('HTTP_REFERER', 'client_list'),
        'dependents_check': True,
        'dependents_count': Project.objects.filter(client=client).count(),
        'dependents_type': 'Projekte'
    })
