from django import forms
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import Utilisateur

# Classes Tailwind communes à tous les champs.
# text-base (16 px) empêche l'iPhone de zoomer automatiquement sur le champ.
CLASSES_CHAMP = (
    "mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-base "
    "focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
)


class ChampsStylesMixin:
    """Ajoute le style Tailwind à tous les champs d'un formulaire."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for champ in self.fields.values():
            champ.widget.attrs.setdefault("class", CLASSES_CHAMP)


# --- Formulaires publics ----------------------------------------------------

class InscriptionForm(ChampsStylesMixin, UserCreationForm):
    """Création de compte : email, prénom, nom et mot de passe (2 fois)."""

    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("email", "first_name", "last_name")
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        # En minuscules AVANT la vérification d'unicité : « Marie@x.cd » est
        # refusé si « marie@x.cd » existe déjà.
        return self.cleaned_data["email"].strip().lower()


class ConnexionForm(ChampsStylesMixin, AuthenticationForm):
    """Connexion par email, sans tenir compte des majuscules."""

    # Django appelle toujours ce champ « username », même s'il contient l'email.
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


# --- Formulaires de l'admin -------------------------------------------------

class UtilisateurAdminCreationForm(AdminUserCreationForm):
    """Formulaire d'ajout dans l'admin : email à la place du nom d'utilisateur."""

    class Meta(AdminUserCreationForm.Meta):
        model = Utilisateur
        fields = ("email",)


class UtilisateurChangeForm(UserChangeForm):
    """Formulaire de modification dans l'admin."""

    class Meta(UserChangeForm.Meta):
        model = Utilisateur