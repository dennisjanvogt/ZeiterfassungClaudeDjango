
from .models import Organization, UserProfile


def organization_context(request):
    """
    Context Processor, der die aktuelle Organisation und alle verfügbaren Organisationen
    des Benutzers in den Template-Kontext einfügt.
    """
    context = {
        'current_organization': None,
        'user_organizations': []
    }
    
    if request.user.is_authenticated:
        # Aktuelle Organisation aus dem Request
        if hasattr(request, 'organization'):
            context['current_organization'] = request.organization
        
        # Alle Organisationen des Benutzers
        if request.user.is_staff or request.user.is_superuser:
            # Administratoren können alle Organisationen sehen
            context['user_organizations'] = Organization.objects.filter(is_active=True)
        else:
            # Normale Benutzer sehen nur ihre eigenen Organisationen
            profiles = UserProfile.objects.filter(user=request.user)
            context['user_organizations'] = [profile.organization for profile in profiles]
    
    return context