from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from tracking.models import Organization, UserProfile
from tracking.forms import RegistrationForm, CustomAuthenticationForm




def custom_login_view(request):
    """
    View für den Login mit freier Organisations-Eingabe
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            # Die Organisation wird bereits in der Form-Validierung geprüft
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            organization_name = form.cleaned_data.get('organization_name')

            # Bei erfolgreicher Validierung ist die Organisation bereits geprüft
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Die Organization ist bereits in cleaned_data
                organization = Organization.objects.get(
                    name__iexact=organization_name.strip(),
                    is_active=True
                )

                # Speichere die aktuelle Organisation in der Session
                request.session['current_organization_id'] = organization.id
                request.session['current_organization_name'] = organization.name

                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'tracking/login.html', {'form': form})


def register_view(request):
    """
    View für die Benutzerregistrierung
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Das Speichern wurde bereits in der Form-Validierung behandelt
            user = form.save()

            # Authentifiziere den Benutzer
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)

            if user is not None:
                messages.success(
                    request,
                    "Deine Registrierung war erfolgreich! Ein Administrator wird dein Konto überprüfen und freischalten."
                )
                return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'tracking/register.html', {'form': form})