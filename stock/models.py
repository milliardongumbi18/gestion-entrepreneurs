from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from entreprises.models import EntrepriseQuerySet, ModeleEntreprise


class Unite(models.TextChoices):
    PIECE = "piece", "Pièce"
    CARTON = "carton", "Carton"
    SAC = "sac", "Sac"
    BOUTEILLE = "bouteille", "Bouteille"
    PAQUET = "paquet", "Paquet"


class TypeMouvement(models.TextChoices):
    ENTREE = "entree", "Entrée (réapprovisionnement)"
    VENTE = "vente", "Sortie (vente)"
    ANNULATION = "annulation", "Retour (annulation de vente)"
    AJUSTEMENT = "ajustement", "Ajustement (inventaire, perte, casse)"


# ---------------------------------------------------------------------------
# Produit
# ---------------------------------------------------------------------------

class ProduitQuerySet(EntrepriseQuerySet):
    """Hérite de .de(entreprise) et ajoute des filtres métier."""

    def actifs(self):
        return self.filter(actif=True)

    def en_alerte(self):
        # F() compare deux colonnes de la même ligne, directement en SQL.
        return self.actifs().filter(quantite_stock__lte=F("seuil_alerte"))


class Produit(ModeleEntreprise):
    nom = models.CharField("nom", max_length=150)
    reference = models.CharField("référence", max_length=50, blank=True, help_text="Code interne (facultatif).")
    unite = models.CharField("unité", max_length=20, choices=Unite.choices, default=Unite.PIECE)
    prix_achat = models.DecimalField(
        "prix d'achat", max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Dans la devise de référence de l'entreprise.",
    )
    prix_vente = models.DecimalField(
        "prix de vente", max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Dans la devise de référence de l'entreprise.",
    )
    # PositiveIntegerField : la base refuse toute valeur négative (contrainte CHECK).
    quantite_stock = models.PositiveIntegerField("quantité en stock", default=0)
    seuil_alerte = models.PositiveIntegerField(
        "seuil d'alerte", default=5,
        help_text="Une alerte apparaît quand le stock descend à ce niveau ou en dessous.",
    )
    actif = models.BooleanField("actif", default=True, help_text="Décocher pour archiver sans supprimer.")

    objects = ProduitQuerySet.as_manager()

    class Meta:
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ["nom"]
        indexes = [models.Index(fields=["entreprise", "actif"], name="produit_entreprise_actif_idx")]
        constraints = [
            # « Riz 25 kg » et « riz 25 KG » = même produit dans une même entreprise.
            models.UniqueConstraint(Lower("nom"), F("entreprise"), name="produit_nom_unique_par_entreprise"),
            # Référence unique dans l'entreprise, seulement si elle est renseignée.
            models.UniqueConstraint(
                fields=["entreprise", "reference"],
                condition=~Q(reference=""),
                name="produit_reference_unique_par_entreprise",
            ),
            models.CheckConstraint(condition=Q(prix_achat__gte=0), name="produit_prix_achat_positif"),
            models.CheckConstraint(condition=Q(prix_vente__gte=0), name="produit_prix_vente_positif"),
        ]

    def __str__(self):
        return self.nom

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def marge_unitaire(self):
        return self.prix_vente - self.prix_achat


# ---------------------------------------------------------------------------
# Mouvement de stock : l'historique de chaque changement
# ---------------------------------------------------------------------------

class MouvementStock(ModeleEntreprise):
    # PROTECT : impossible de supprimer un produit qui a un historique.
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="mouvements", verbose_name="produit")
    type = models.CharField("type", max_length=20, choices=TypeMouvement.choices)
    # Positif = le stock augmente, négatif = le stock diminue.
    quantite = models.IntegerField("quantité")
    cout_unitaire = models.DecimalField(
        "coût unitaire", max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Prix d'achat payé lors d'une entrée.",
    )
    note = models.CharField("note", max_length=255, blank=True)
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mouvements_stock", verbose_name="auteur",
    )

    class Meta:
        verbose_name = "mouvement de stock"
        verbose_name_plural = "mouvements de stock"
        ordering = ["-cree_le"]
        constraints = [
            models.CheckConstraint(condition=~Q(quantite=0), name="mouvement_quantite_non_nulle"),
        ]

    def save(self, *args, **kwargs):
        # Le mouvement appartient TOUJOURS à l'entreprise du produit : aucun mélange possible.
        if self.entreprise_id is None:
            self.entreprise_id = self.produit.entreprise_id
        elif self.entreprise_id != self.produit.entreprise_id:
            raise ValueError("Le mouvement et le produit doivent appartenir à la même entreprise.")
        super().save(*args, **kwargs)

    def __str__(self):
        signe = "+" if self.quantite > 0 else ""
        return f"{self.get_type_display()} : {signe}{self.quantite} × {self.produit}"