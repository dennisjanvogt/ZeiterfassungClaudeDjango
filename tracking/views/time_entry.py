from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from tracking.models import Project, TimeEntry
from datetime import datetime
from decimal import Decimal


@login_required
def time_entry(request):
    # Nur den eigenen aktiven Timer anzeigen
    active_timer = TimeEntry.objects.filter(
        user=request.user, end_time__isnull=True).first()

    # Alle Projekte anzeigen (unabhängig vom Benutzer)
    projects = Project.objects.filter(
        is_active=True).order_by('client__name', 'name')

    if request.method == 'POST':
        # Manueller Eintrag
        if 'submit_manual' in request.POST:
            project_id = request.POST.get('project')
            description = request.POST.get('description', '')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            is_billable = 'is_billable' in request.POST

            # Get factored_hours if provided
            factored_hours = request.POST.get('factored_hours')
            if factored_hours and factored_hours.strip():
                try:
                    factored_hours = Decimal(factored_hours.replace(',', '.'))
                except:
                    factored_hours = None
            else:
                factored_hours = None

            try:
                project = Project.objects.get(id=project_id)
                start_time = timezone.make_aware(
                    datetime.strptime(start_time, '%Y-%m-%dT%H:%M'))
                end_time = timezone.make_aware(
                    datetime.strptime(end_time, '%Y-%m-%dT%H:%M'))

                duration_seconds = (end_time - start_time).total_seconds()
                duration_hours = duration_seconds / 3600

                # Erstelle Zeiteintrag für den aktuellen Benutzer
                entry = TimeEntry.objects.create(
                    project=project,
                    user=request.user,  # Aktueller Benutzer
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration_hours,
                    is_billable=is_billable,
                    factored_hours=factored_hours  # Save the factored hours
                )

                messages.success(
                    request, "Zeiteintrag erfolgreich gespeichert.")

                # Debug message for factored hours
                if factored_hours:
                    messages.info(
                        request, f"Fakturierte Stunden: {factored_hours} h")
            except Exception as e:
                messages.error(request, f"Fehler beim Speichern: {str(e)}")

            return redirect('time_entry')

        # Timer starten
        elif 'start_timer' in request.POST:
            if active_timer:
                messages.warning(
                    request, "Es läuft bereits ein Timer. Bitte stoppe diesen zuerst.")
                return redirect('time_entry')

            project_id = request.POST.get('project')
            description = request.POST.get('description', '')
            is_billable = 'is_billable' in request.POST

            try:
                project = Project.objects.get(id=project_id)

                # Erstelle Zeiteintrag für den aktuellen Benutzer
                entry = TimeEntry.objects.create(
                    project=project,
                    user=request.user,  # Aktueller Benutzer
                    description=description,
                    start_time=timezone.now(),
                    is_billable=is_billable
                )

                messages.success(
                    request, f"Timer für '{project.name}' gestartet.")
            except Exception as e:
                messages.error(
                    request, f"Fehler beim Starten des Timers: {str(e)}")

            return redirect('time_entry')

    # Nur die eigenen kürzlich erstellten Einträge anzeigen
    recent_entries = TimeEntry.objects.filter(
        user=request.user).order_by('-start_time')[:10]

    return render(request, 'tracking/time_entry.html', {
        'active_timer': active_timer,
        'projects': projects,
        'recent_entries': recent_entries,
    })


@login_required
def stop_timer(request, entry_id):
    entry = get_object_or_404(TimeEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        if entry.end_time is None:
            entry.end_time = timezone.now()
            duration_seconds = (
                entry.end_time - entry.start_time).total_seconds()
            entry.duration = duration_seconds / 3600
            entry.save()

            rounded_duration = entry.get_rounded_duration()
            messages.success(request,
                             f"Timer für '{entry.project.name}' gestoppt. Dauer: {rounded_duration} Stunden.")

    return redirect('time_entry')


@login_required
def edit_time_entry(request, entry_id):
    entry = get_object_or_404(TimeEntry, id=entry_id, user=request.user)
    projects = Project.objects.filter(
        is_active=True).order_by('client__name', 'name')

    if request.method == 'POST':
        # Aktualisierte Daten aus dem Formular abrufen
        project_id = request.POST.get('project')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_billable = 'is_billable' in request.POST

        # Prüfen ob factored_hours im Formular übermittelt wurde
        if 'factored_hours' in request.POST:
            factored_hours = request.POST.get('factored_hours')

            # Wenn ein Wert eingegeben wurde, diesen verwenden
            if factored_hours and factored_hours.strip():
                try:
                    factored_hours = Decimal(factored_hours.replace(',', '.'))
                except Exception as e:
                    print(f"Error converting factored_hours: {e}")
                    # Bei Fehler bei der Konvertierung den vorherigen Wert beibehalten
                    factored_hours = entry.factored_hours
            else:
                # Wenn das Feld leer ist, auf None setzen (automatische Berechnung)
                factored_hours = None
        else:
            # Wenn das Feld nicht übermittelt wurde, vorherigen Wert beibehalten
            factored_hours = entry.factored_hours

        try:
            # Daten verarbeiten und speichern
            project = Project.objects.get(id=project_id)
            start_time = timezone.make_aware(
                datetime.strptime(start_time, '%Y-%m-%dT%H:%M'))
            end_time = timezone.make_aware(
                datetime.strptime(end_time, '%Y-%m-%dT%H:%M'))

            # Dauer neu berechnen
            duration_seconds = (end_time - start_time).total_seconds()
            duration_hours = duration_seconds / 3600

            # Eintrag aktualisieren
            entry.project = project
            entry.description = description
            entry.start_time = start_time
            entry.end_time = end_time
            entry.duration = duration_hours
            entry.is_billable = is_billable
            entry.factored_hours = factored_hours  # Explizit factored_hours setzen
            entry.save()

            messages.success(request, "Zeiteintrag erfolgreich aktualisiert.")

            # Debug-Nachricht für factored_hours
            if factored_hours is not None:
                messages.info(
                    request, f"Fakturierte Stunden aktualisiert: {factored_hours} h")
            else:
                messages.info(
                    request, "Fakturierte Stunden zurückgesetzt auf automatische Berechnung.")

            return redirect('time_entry')

        except Exception as e:
            messages.error(request, f"Fehler beim Aktualisieren: {str(e)}")

    # DateTime-Format für HTML5 datetime-local Input vorbereiten
    start_time_local = entry.start_time.strftime('%Y-%m-%dT%H:%M')
    end_time_local = entry.end_time.strftime(
        '%Y-%m-%dT%H:%M') if entry.end_time else ''

    # Bei der ersten Anzeige des Formulars existierenden faktorierten Wert verwenden
    # oder den automatisch berechneten, wenn kein Wert gesetzt ist
    factored_hours = entry.factored_hours

    # Explizit factored_hours im Kontext übergeben
    context = {
        'entry': entry,
        'projects': projects,
        'start_time_local': start_time_local,
        'end_time_local': end_time_local,
        'factored_hours': factored_hours,
    }

    return render(request, 'tracking/edit_time_entry.html', context)


@login_required
def delete_time_entry(request, entry_id):
    entry = get_object_or_404(TimeEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        # Speichere Projektname für Erfolgsbenachrichtigung
        project_name = entry.project.name
        entry_date = entry.start_time.strftime('%d.%m.%Y')

        # Lösche den Zeiteintrag
        entry.delete()

        messages.success(
            request, f'Zeiteintrag für "{project_name}" vom {entry_date} wurde gelöscht.')

        # Zurück zur vorherigen Seite oder zur Zeiterfassung
        next_url = request.POST.get('next', 'time_entry')
        return redirect(next_url)

    return render(request, 'tracking/confirm_delete.html', {
        'object': entry,
        'object_name': f'Zeiteintrag für "{entry.project.name}" vom {entry.start_time.strftime("%d.%m.%Y")}',
        'back_url': request.META.get('HTTP_REFERER', 'time_entry')
    })
