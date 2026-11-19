from django.contrib import admin

from .models import Client, LigneVente, Vente


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "entreprise")
    list_filter = ("entreprise",)
    search_fields = ("nom", "telephone", "email")
    list_select_related = ("entreprise",)


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    can_delete = False
    fields = ("produit", "quantite", "prix_unitaire", "prix_achat_unitaire")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    """Consultation seule : une vente se crée et s'annule par les services (stock cohérent)."""

    list_display = ("numero", "date", "entreprise", "client", "total", "devise", "mode_paiement", "statut")
    list_filter = ("statut", "devise", "mode_paiement", "entreprise")
    search_fields = ("numero", "client__nom")
    date_hierarchy = "date"
    list_select_related = ("entreprise", "client")
    inlines = [LigneVenteInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False