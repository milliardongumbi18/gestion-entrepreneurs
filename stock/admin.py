from django.contrib import admin

from .models import MouvementStock, Produit


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "entreprise", "prix_vente", "quantite_stock", "alerte", "actif")
    list_filter = ("actif", "entreprise")
    search_fields = ("nom", "reference")
    list_select_related = ("entreprise",)  # évite une requête par ligne
    # Le stock ne se modifie QUE par des mouvements (traçabilité).
    readonly_fields = ("quantite_stock", "cree_le", "modifie_le")

    @admin.display(boolean=True, description="alerte")
    def alerte(self, obj):
        return obj.en_alerte


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    """Historique en lecture seule : on ne réécrit pas le passé."""

    list_display = ("cree_le", "produit", "type", "quantite", "auteur", "entreprise")
    list_filter = ("type", "entreprise")
    search_fields = ("produit__nom", "note")
    list_select_related = ("produit", "auteur", "entreprise")

    def has_add_permission(self, request):
        return False  # seuls enregistrer_mouvement() et les ventes créent des mouvements

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False