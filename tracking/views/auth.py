from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from tracking.forms import RegistrationForm, CustomAuthenticationForm
from tracking.models import UserProfile


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Benutzer erstellen, aber noch nicht speichern
            user = form.save(commit=False)
            # Benutzer ist aktiv (kann aber nicht einloggen bis genehmigt)
            user.is_active = True
            user.save()

            # Profil erstellen (standardmäßig nicht genehmigt)
            UserProfile.objects.create(user=user, is_approved=False)

            messages.success(
                request,
                "Deine Registrierung war erfolgreich! Ein Administrator wird dein Konto überprüfen und freischalten. "
                "Du erhältst eine Benachrichtigung, sobald dein Konto freigeschaltet wurde."
            )
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'tracking/register.html', {'form': form})


def custom_login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'tracking/login.html', {'form': form})
