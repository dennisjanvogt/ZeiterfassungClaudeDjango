from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from tracking.models import TimeEntry, UserProfile
from tracking.forms import ProfileForm


@login_required
def profile_view(request):
    """Zeigt das Benutzerprofil an."""
    # UserProfile erstellen, falls es noch nicht existiert
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user)

    # Zusammenfassen der Monatsstunden und des Monatsumsatzes für die Profilseite
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Monatsstunden und Monatsumsatz berechnen
    month_entries = TimeEntry.objects.filter(
        user=request.user,
        start_time__date__gte=month_start,
        start_time__date__lte=today
    )
    month_hours = sum(entry.get_rounded_duration() for entry in month_entries)
    month_revenue = sum(entry.get_billable_amount() for entry in month_entries)

    # Gesamtstunden und Gesamtumsatz berechnen
    total_entries = TimeEntry.objects.filter(user=request.user)
    total_hours = sum(entry.get_rounded_duration() for entry in total_entries)
    total_revenue = sum(entry.get_billable_amount() for entry in total_entries)

    context = {
        'user_profile': user_profile,
        'month_hours': month_hours,
        'month_revenue': month_revenue,
        'total_hours': total_hours,
        'total_revenue': total_revenue,
    }

    return render(request, 'tracking/profile.html', context)


@login_required
def edit_profile(request):
    """View zum Bearbeiten des eigenen Benutzerprofils mit Formular-Integration"""
    user = request.user

    # Profile-Objekt laden oder erstellen falls noch nicht vorhanden
    try:
        profile = user.profile
    except:
        profile = UserProfile.objects.create(user=user, is_approved=True)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user, user=user)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Ihr Profil wurde erfolgreich aktualisiert.')
            return redirect('edit_profile')
    else:
        form = ProfileForm(instance=user, user=user)

    context = {
        'user': user,
        'profile': profile,
        'form': form
    }

    return render(request, 'tracking/edit_profile.html', context)


@login_required
def change_password(request):
    """View zum Ändern des Passworts"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validierung
        if not request.user.check_password(current_password):
            messages.error(request, 'Das aktuelle Passwort ist nicht korrekt.')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(
                request, 'Die neuen Passwörter stimmen nicht überein.')
            return redirect('change_password')

        if len(new_password) < 8:
            messages.error(
                request, 'Das neue Passwort muss mindestens 8 Zeichen lang sein.')
            return redirect('change_password')

        # Passwort ändern
        request.user.set_password(new_password)
        request.user.save()

        # Benutzer neu anmelden, damit die Sitzung nicht verloren geht
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Ihr Passwort wurde erfolgreich geändert.')
        return redirect('edit_profile')

    return render(request, 'tracking/change_password.html')
