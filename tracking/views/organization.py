
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tracking.models import Organization, UserProfile


@login_required
def switch_organization(request, organization_id):
    """
    Wechselt die aktuelle Organisation für den angemeldeten Benutzer.
    """
    # Administratoren können zu jeder Organisation wechseln
    if request.user.is_staff or request.user.is_superuser:
        organization = get_object_or_404(Organization, id=organization_id, is_active=True)
    else:
        # Normale Benutzer können nur zu Organisationen wechseln, denen sie zugewiesen sind
        organization = get_object_or_404(
            Organization, 
            id=organization_id, 
            is_active=True,
            user_profiles__user=request.user
        )
    
    # Organisationsinformationen in der Session aktualisieren
    request.session['current_organization_id'] = organization.id
    request.session['current_organization_name'] = organization.name
    request.session['current_organization_slug'] = organization.slug
    
    messages.success(request, f"Du bist jetzt mit der Organisation '{organization.name}' verbunden.")
    
    # Zurück zur vorherigen Seite oder zum Dashboard
    next_url = request.GET.get('next', 'dashboard')
    return redirect(next_url)