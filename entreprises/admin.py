from django.contrib import admin
from django.db.models import Count

from .models import Entreprise, Invitation, Membre


class MembreInline(admin.TabularInline):
    model = Membre
    extra = 0
    autocomplete_fields = ["utilisateur"]  # recherche par email (search_fields de l'admin Utilisateur)
    fields = ("utilisateur", "role", "cree_le")
    readonly_fields = ("cree_le",)


class InvitationInline(admin.TabularInline):
    model = Invitation
    extra = 0
    fields = ("email", "role", "expire_le", "acceptee_le", "token")
    readonly_fields = ("acceptee_le", "token")


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "devise_reference", "taux_usd_cdf", "nombre_membres", "cree_le")
    list_filter = ("devise_reference", "ville")
    search_fields = ("nom", "telephone")
    inlines = [MembreInline, InvitationInline]

    def get_queryset(self, request):
        # Le nombre de membres est calculé en UNE requête SQL pour toute la liste,
        # au lieu d'une requête par ligne (problème « N+1 »).
        return super().get_queryset(request).annotate(nb_membres=Count("membres"))

    @admin.display(description="membres", ordering="nb_membres")
    def nombre_membres(self, obj):
        return obj.nb_membres