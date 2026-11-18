from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UtilisateurAdminCreationForm, UtilisateurChangeForm
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """
    L'admin utilisateur de Django fait référence à « username » partout :
    on redéfinit donc les listes de champs avec « email ».
    """

    form = UtilisateurChangeForm
    add_form = UtilisateurAdminCreationForm
    model = Utilisateur

    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )