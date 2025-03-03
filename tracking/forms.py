from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Client, Project, TimeEntry, UserProfile

# Formulare für die Hauptfunktionalität der App


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

# Formulare für Benutzerregistrierung und -authentifizierung


class RegistrationForm(UserCreationForm):
    """
    Formular für die Benutzerregistrierung mit Codewort-Validierung und
    zusätzlichen Feldern für E-Mail, Vorname und Nachname.
    """
    codewort = forms.CharField(
        max_length=50,
        required=True,
        help_text="Bitte gib das Registrierungs-Codewort ein",
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
                  'password1', 'password2', 'codewort')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_codewort(self):
        """Überprüft, ob das richtige Codewort eingegeben wurde."""
        codewort = self.cleaned_data.get('codewort')
        if codewort != "Lunatec":
            raise ValidationError(
                "Das eingegebene Codewort ist nicht korrekt.")
        return codewort

    def clean_email(self):
        """Überprüft, ob die E-Mail-Adresse bereits verwendet wird."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Diese E-Mail-Adresse wird bereits verwendet.")
        return email


class CustomAuthenticationForm(forms.Form):
    """
    Angepasstes Login-Formular, das auch prüft, ob der Benutzer bereits vom
    Admin genehmigt wurde.
    """
    username = forms.CharField(
        max_length=254,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Überprüfen, ob der Benutzer existiert und das Passwort stimmt
            user = authenticate(username=username, password=password)

            if user is None:
                raise ValidationError("Ungültiger Benutzername oder Passwort.")

            # Für Admin-Benutzer kein Profil erforderlich
            if user.is_staff or user.is_superuser:
                # Automatisch ein genehmigtes Profil erstellen, falls keines existiert
                from .models import UserProfile
                from django.utils import timezone

                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'is_approved': True,
                              'approval_date': timezone.now()}
                )
            else:
                # Überprüfen, ob der Benutzer vom Admin genehmigt wurde
                try:
                    profile = user.profile
                    if not profile.is_approved:
                        raise ValidationError(
                            "Dein Konto wurde noch nicht von einem Administrator freigegeben. "
                            "Bitte warte auf die Freigabe oder kontaktiere einen Administrator."
                        )
                except:
                    # Erstelle ein nicht genehmigtes Profil für normale Benutzer
                    from .models import UserProfile
                    UserProfile.objects.create(user=user, is_approved=False)

                    raise ValidationError(
                        "Dein Konto wurde noch nicht von einem Administrator freigegeben. "
                        "Bitte warte auf die Freigabe oder kontaktiere einen Administrator."
                    )

            # Überprüfen, ob der Benutzer aktiv ist
            if not user.is_active:
                raise ValidationError("Dieses Konto ist deaktiviert.")

        return cleaned_data

# Ergänzung für tracking/forms.py - Formular-Definitionen für Profilfunktionen


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
