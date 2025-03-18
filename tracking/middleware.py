# tracking/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import Organization, UserProfile


class OrganizationMiddleware:
    """
    Middleware zur Verarbeitung der aktuellen Organisation im Request-Kontext.
    Stellt sicher, dass ein angemeldeter Benutzer nur auf Daten seiner eigenen Organisation zugreifen kann.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Middleware-Code wird vor dem View ausgeführt
        
        # Wenn der Benutzer angemeldet ist
        if request.user.is_authenticated:
            # Prüfen, ob eine aktuelle Organisation in der Session gespeichert ist
            current_org_id = request.session.get('current_organization_id')
            
            if not current_org_id:
                # Wenn keine aktuelle Organisation in der Session ist, die erste Organisation des Benutzers verwenden
                try:
                    user_profile = UserProfile.objects.filter(user=request.user).first()
                    if user_profile:
                        org = user_profile.organization
                        request.session['current_organization_id'] = org.id
                        request.session['current_organization_name'] = org.name
                        request.session['current_organization_slug'] = org.slug
                except UserProfile.DoesNotExist:
                    # Wenn der Benutzer kein Profil hat und kein Admin ist, zur Anmeldeseite umleiten
                    if not request.user.is_staff and not request.user.is_superuser:
                        messages.error(request, "Du bist keiner Organisation zugewiesen. Bitte wende dich an einen Administrator.")
                        return redirect('logout')
            
            # Aktuelle Organisation dem Request-Objekt hinzufügen
            if current_org_id:
                try:
                    request.organization = Organization.objects.get(id=current_org_id)
                except Organization.DoesNotExist:
                    # Organisation existiert nicht mehr, Session-Daten löschen
                    del request.session['current_organization_id']
                    del request.session['current_organization_name']
                    del request.session['current_organization_slug']
                    messages.error(request, "Die ausgewählte Organisation existiert nicht mehr.")
                    return redirect('logout')
            
            # Für Admins eine spezielle Behandlung
            if request.user.is_staff or request.user.is_superuser:
                # Admins können alle Organisationen sehen, wenn sie keine spezifische ausgewählt haben
                if not hasattr(request, 'organization'):
                    # Standardmäßig die erste aktive Organisation verwenden
                    org = Organization.objects.filter(is_active=True).first()
                    if org:
                        request.organization = org
                        request.session['current_organization_id'] = org.id
                        request.session['current_organization_name'] = org.name
                        request.session['current_organization_slug'] = org.slug
        
        # Anfrage an den nächsten Middleware-Handler oder View weiterleiten
        response = self.get_response(request)
        
        # Middleware-Code wird nach dem View ausgeführt
        return response