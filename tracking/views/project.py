from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tracking.models import Client, Project, TimeEntry
from tracking.forms import ProjectForm


@login_required
def project_list(request):
    projects = Project.objects.all().order_by('client__name', 'name')
    clients = Client.objects.all()

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm()

    return render(request, 'tracking/project_list.html', {
        'projects': projects,
        'clients': clients,
        'form': form
    })


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    time_entries = project.time_entries.all()

    used_hours = project.get_used_hours()
    remaining_hours = project.get_remaining_hours()
    percentage_used = project.get_percentage_used()

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'tracking/project_detail.html', {
        'project': project,
        'time_entries': time_entries,
        'form': form,
        'used_hours': used_hours,
        'remaining_hours': remaining_hours,
        'percentage_used': percentage_used,
    })


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Prüfen, ob der Benutzer berechtigt ist (optional)
    if not request.user.is_staff:
        messages.error(
            request, "Sie haben keine Berechtigung, Projekte zu löschen.")
        return redirect('project_list')

    if request.method == 'POST':
        # Prüfen, ob noch Zeiteinträge existieren
        time_entries_count = TimeEntry.objects.filter(project=project).count()

        if time_entries_count > 0:
            messages.error(
                request,
                f'Das Projekt "{project.name}" kann nicht gelöscht werden, da es noch {time_entries_count} Zeiteinträge enthält. '
                f'Bitte löschen Sie zuerst alle zugehörigen Zeiteinträge.'
            )
            return redirect('project_detail', project_id=project.id)

        # Speichere Projektname für Erfolgsbenachrichtigung
        project_name = project.name

        # Lösche das Projekt
        project.delete()

        messages.success(
            request, f'Projekt "{project_name}" wurde erfolgreich gelöscht.')
        return redirect('project_list')

    return render(request, 'tracking/confirm_delete.html', {
        'object': project,
        'object_name': f'Projekt "{project.name}"',
        'back_url': request.META.get('HTTP_REFERER', 'project_list'),
        'dependents_check': True,
        'dependents_count': TimeEntry.objects.filter(project=project).count(),
        'dependents_type': 'Zeiteinträge'
    })
