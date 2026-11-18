from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Utilisateur


class UtilisateurAdminCreationForm(AdminUserCreationForm):
    """Formulaire d'ajout dans l'admin : email à la place du nom d'utilisateur."""

    class Meta(AdminUserCreationForm.Meta):
        model = Utilisateur
        fields = ("email",)


class UtilisateurChangeForm(UserChangeForm):
    """Formulaire de modification dans l'admin."""

    class Meta(UserChangeForm.Meta):
        model = Utilisateur