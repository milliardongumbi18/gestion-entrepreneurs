from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from entreprises.models import Devise, EntrepriseQuerySet, ModeleEntreprise
from stock.models import Produit


class ModePaiement(models.TextChoices):
    ESPECES = "especes", "Espèces"
    MOBILE_MONEY = "mobile_money", "Mobile money"
    CARTE = "carte", "Carte bancaire"
    VIREMENT = "virement", "Virement"


class StatutVente(models.TextChoices):
    VALIDEE = "validee", "Validée"
    ANNULEE = "annulee", "Annulée"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class Client(ModeleEntreprise):
    nom = models.CharField("nom", max_length=150)
    telephone = models.CharField("téléphone", max_length=30, blank=True)
    email = models.EmailField("email", blank=True)
    adresse = models.CharField("adresse", max_length=255, blank=True)

    class Meta:
        verbose_name = "client"
        verbose_name_plural = "clients"
        ordering = ["nom"]
        constraints = [
            # Un même numéro de téléphone ne désigne qu'un client par entreprise (s'il est renseigné).
            models.UniqueConstraint(
                fields=["entreprise", "telephone"],
                condition=~Q(telephone=""),
                name="client_telephone_unique_par_entreprise",
            ),
        ]

    def __str__(self):
        return self.nom


# ---------------------------------------------------------------------------
# Vente
# ---------------------------------------------------------------------------

class VenteQuerySet(EntrepriseQuerySet):
    def validees(self):
        """Les ventes annulées ne comptent pas dans le chiffre d'affaires."""
        return self.filter(statut=StatutVente.VALIDEE)


class Vente(ModeleEntreprise):
    numero = models.CharField("numéro", max_length=20, editable=False)
    date = models.DateTimeField("date", default=timezone.now)
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ventes", verbose_name="client",
    )
    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ventes_realisees", verbose_name="vendeur",
    )
    devise = models.CharField("devise", max_length=3, choices=Devise.choices)
    taux_change = models.DecimalField(
        "taux USD → CDF", max_digits=12, decimal_places=2,
        help_text="Copie figée du taux au moment de la vente.",
    )
    total = models.DecimalField("total", max_digits=14, decimal_places=2, default=0,
                                help_text="Dans la devise de la vente.")
    total_reference = models.DecimalField("total (devise de référence)", max_digits=14, decimal_places=2, default=0)
    cout_reference = models.DecimalField(
        "coût d'achat (devise de référence)", max_digits=14, decimal_places=2, default=0,
        help_text="Coût d'achat des produits vendus : sert au calcul du bénéfice.",
    )
    mode_paiement = models.CharField("mode de paiement", max_length=20,
                                     choices=ModePaiement.choices, default=ModePaiement.ESPECES)
    statut = models.CharField("statut", max_length=10, choices=StatutVente.choices, default=StatutVente.VALIDEE)
    annulee_le = models.DateTimeField("annulée le", null=True, blank=True)
    note = models.CharField("note", max_length=255, blank=True)

    objects = VenteQuerySet.as_manager()

    class Meta:
        verbose_name = "vente"
        verbose_name_plural = "ventes"
        ordering = ["-date"]
        # Le tableau de bord filtrera toujours par entreprise ET par période.
        indexes = [models.Index(fields=["entreprise", "date"], name="vente_entreprise_date_idx")]
        constraints = [
            models.UniqueConstraint(fields=["entreprise", "numero"], name="vente_numero_unique_par_entreprise"),
            models.CheckConstraint(condition=Q(taux_change__gt=0), name="vente_taux_positif"),
            models.CheckConstraint(condition=Q(total__gte=0), name="vente_total_positif"),
        ]

    def __str__(self):
        return self.numero

    @property
    def marge_reference(self):
        return self.total_reference - self.cout_reference


# ---------------------------------------------------------------------------
# Ligne de vente
# ---------------------------------------------------------------------------

class LigneVente(models.Model):
    """Pas de champ entreprise : une ligne appartient à sa vente, qui appartient à l'entreprise."""

    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="lignes", verbose_name="vente")
    # PROTECT : un produit déjà vendu ne peut pas être supprimé (il sera archivé).
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="lignes_vente", verbose_name="produit")
    quantite = models.PositiveIntegerField("quantité")
    prix_unitaire = models.DecimalField("prix unitaire", max_digits=14, decimal_places=2,
                                        help_text="Dans la devise de la vente, copié au moment de la vente.")
    prix_achat_unitaire = models.DecimalField("prix d'achat unitaire", max_digits=14, decimal_places=2,
                                              help_text="Dans la devise de référence, copié au moment de la vente.")

    class Meta:
        verbose_name = "ligne de vente"
        verbose_name_plural = "lignes de vente"
        constraints = [
            models.CheckConstraint(condition=Q(quantite__gt=0), name="ligne_quantite_positive"),
            models.UniqueConstraint(fields=["vente", "produit"], name="ligne_produit_unique_par_vente"),
        ]

    def __str__(self):
        return f"{self.quantite} × {self.produit}"

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite