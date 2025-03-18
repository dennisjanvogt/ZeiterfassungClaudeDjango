from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Client, Project, TimeEntry, UserProfile, Organization


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'contact_person', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['client', 'name', 'description',
                  'hourly_rate', 'total_hours', 'is_active']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['project', 'description',
                  'start_time', 'end_time', 'is_billable']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomAuthenticationForm(forms.Form):
    """
    Angepasstes Login-Formular mit freier Organisations-Eingabe
    """
    organization_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Organisationsname',
            'autofocus': True
        }),
        label="Organisation"
    )
    
    username = forms.CharField(
        max_length=254,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Benutzername'}),
        label="Benutzername"
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Passwort'
        }),
        label="Passwort"
    )

    def clean(self):
        cleaned_data = super().clean()
        organization_name = cleaned_data.get('organization_name')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if organization_name and username and password:
            # Versuche, die Organisation zu finden (case-insensitive)
            try:
                organization = Organization.objects.get(
                    name__iexact=organization_name.strip(),
                    is_active=True
                )
            except Organization.DoesNotExist:
                raise ValidationError(
                    "Die angegebene Organisation existiert nicht oder ist nicht aktiv."
                )

            # Suche den Benutzer NUR in dieser Organisation
            try:
                user_profile = UserProfile.objects.get(
                    user__username=username, 
                    organization=organization
                )
                
                user = user_profile.user

                # Passwort-Überprüfung
                if not user.check_password(password):
                    raise ValidationError("Ungültiger Benutzername oder Passwort.")
                
                # Prüfe, ob der Benutzer genehmigt ist
                if not user.is_staff and not user.is_superuser and not user_profile.is_approved:
                    raise ValidationError(
                        "Dein Konto wurde noch nicht von einem Administrator freigegeben. "
                        "Bitte warte auf die Freigabe oder kontaktiere einen Administrator."
                    )

                # Überprüfen, ob der Benutzer aktiv ist
                if not user.is_active:
                    raise ValidationError("Dieses Konto ist deaktiviert.")

                # Speichere die Organisation im Form-Context
                self.organization = organization
                self.user = user

            except UserProfile.DoesNotExist:
                raise ValidationError(
                    "Benutzer nicht in dieser Organisation gefunden."
                )
                
        return cleaned_data


class RegistrationForm(UserCreationForm):
    """
    Aktualisiertes Formular für die Benutzerregistrierung mit freier Organisations-Eingabe
    """
    organization_name = forms.CharField(
        max_length=255,
        required=True,
        help_text="Name Ihrer Organisation",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    registration_code = forms.CharField(
        max_length=50,
        required=True,
        help_text="Bitte gib den Registrierungs-Code für deine Organisation ein",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text="Bitte gib eine gültige E-Mail-Adresse ein",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password1', 'password2', 'organization_name', 'registration_code')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username']
        organization_name = self.cleaned_data.get('organization_name')
        
        if organization_name:
            # Prüfe, ob der Benutzername in DIESER Organisation bereits existiert
            try:
                organization = Organization.objects.get(
                    name__iexact=organization_name.strip(),
                    is_active=True
                )
                
                # Prüfe nur innerhalb der aktuellen Organisation
                if UserProfile.objects.filter(
                    user__username=username, 
                    organization=organization
                ).exists():
                    raise ValidationError(
                        "Ein Benutzer mit diesem Namen existiert bereits in Ihrer Organisation."
                    )
            except Organization.DoesNotExist:
                pass
        
        return username

    def clean(self):
        cleaned_data = super().clean()
        organization_name = cleaned_data.get('organization_name')
        registration_code = cleaned_data.get('registration_code')
        
        # Versuche, die Organisation zu finden (case-insensitive)
        try:
            organization = Organization.objects.get(
                name__iexact=organization_name.strip(),
                is_active=True
            )
        except Organization.DoesNotExist:
            raise ValidationError(
                "Die angegebene Organisation existiert nicht oder ist nicht aktiv."
            )
        
        # Überprüfe den Registrierungscode
        if registration_code != organization.registration_code:
            raise ValidationError(
                "Der eingegebene Registrierungs-Code ist nicht korrekt."
            )
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Stelle sicher, dass der Benutzer aktiv ist
        user.is_active = True
        
        if commit:
            user.save()
            
            # Organisation finden
            organization = Organization.objects.get(
                name__iexact=self.cleaned_data['organization_name'].strip(),
                is_active=True
            )
            
            # Profil erstellen
            UserProfile.objects.create(
                user=user,
                organization=organization,
                is_approved=False
            )
        
        return user


class ProfileForm(forms.ModelForm):
    """Formular zum Bearbeiten des Benutzerprofils."""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Vorname",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Nachname",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        label="E-Mail",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)

        # Wenn ein Benutzer übergeben wurde, diesen zur späteren Validierung speichern
        self.user = user

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Nur prüfen, wenn ein Benutzer übergeben wurde
        if self.user and email:
            # Prüfen, ob die E-Mail bereits verwendet wird (außer vom aktuellen Benutzer)
            if User.objects.exclude(id=self.user.id).filter(email=email).exists():
                raise forms.ValidationError(
                    "Diese E-Mail-Adresse wird bereits verwendet.")

        return email


class PasswordChangeForm(forms.Form):
    """Formular zum Ändern des Passworts."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Aktuelles Passwort",
        required=True
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Neues Passwort",
        required=True,
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Neues Passwort bestätigen",
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')

        if self.user and not self.user.check_password(current_password):
            raise forms.ValidationError(
                "Das aktuelle Passwort ist nicht korrekt.")

        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password',
                           "Die neuen Passwörter stimmen nicht überein.")

        return cleaned_data