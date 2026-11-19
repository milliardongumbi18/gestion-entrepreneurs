import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


# ---------------------------------------------------------------------------
# Listes de choix réutilisées dans tout le projet
# ---------------------------------------------------------------------------

class Devise(models.TextChoices):
    CDF = "CDF", "Franc congolais (CDF)"
    USD = "USD", "Dollar américain (USD)"


class Role(models.TextChoices):
    PROPRIETAIRE = "proprietaire", "Propriétaire"
    GERANT = "gerant", "Gérant"
    VENDEUR = "vendeur", "Vendeur"


# ---------------------------------------------------------------------------
# Base commune à toutes les données d'une entreprise
# ---------------------------------------------------------------------------

class EntrepriseQuerySet(models.QuerySet):
    def de(self, entreprise):
        """Ne garde que les lignes de cette entreprise : Produit.objects.de(entreprise)."""
        return self.filter(entreprise=entreprise)


class ModeleEntreprise(models.Model):
    """
    Modèle ABSTRAIT : il ne crée pas de table. Chaque modèle qui en hérite
    reçoit automatiquement une entreprise obligatoire et des dates de suivi.
    """

    entreprise = models.ForeignKey(
        "entreprises.Entreprise",
        on_delete=models.CASCADE,
        # « %(class)ss » = nom de la classe en minuscules + « s » :
        # Membre -> entreprise.membres, Invitation -> entreprise.invitations, etc.
        related_name="%(class)ss",
        verbose_name="entreprise",
    )
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    modifie_le = models.DateTimeField("modifié le", auto_now=True)

    objects = EntrepriseQuerySet.as_manager()

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Entreprise
# ---------------------------------------------------------------------------

class Entreprise(models.Model):
    nom = models.CharField("nom de l'entreprise", max_length=150)
    telephone = models.CharField("téléphone", max_length=30, blank=True)
    adresse = models.CharField("adresse", max_length=255, blank=True)
    ville = models.CharField("ville", max_length=100, default="Kinshasa")
    devise_reference = models.CharField(
        "devise de référence",
        max_length=3,
        choices=Devise.choices,
        default=Devise.CDF,
        help_text="Devise dans laquelle le tableau de bord additionne tous les montants.",
    )
    taux_usd_cdf = models.DecimalField(
        "taux USD → CDF",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Combien de francs congolais pour 1 dollar, aujourd'hui.",
    )
    cree_le = models.DateTimeField("créée le", auto_now_add=True)
    modifie_le = models.DateTimeField("modifiée le", auto_now=True)

    class Meta:
        verbose_name = "entreprise"
        verbose_name_plural = "entreprises"
        ordering = ["nom"]
        constraints = [
            # Garantie au niveau de la base : un taux nul ou négatif est impossible.
            models.CheckConstraint(condition=Q(taux_usd_cdf__gt=0), name="entreprise_taux_positif"),
        ]

    def __str__(self):
        return self.nom


# ---------------------------------------------------------------------------
# Membre : un utilisateur dans UNE entreprise, avec un rôle
# ---------------------------------------------------------------------------

class Membre(ModeleEntreprise):
    # OneToOne : la base refuse qu'un utilisateur appartienne à deux entreprises (décision V1).
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membre",
        verbose_name="utilisateur",
    )
    role = models.CharField("rôle", max_length=20, choices=Role.choices, default=Role.VENDEUR)

    class Meta:
        verbose_name = "membre"
        verbose_name_plural = "membres"
        ordering = ["entreprise", "role"]
        constraints = [
            # Contrainte « partielle » : l'unicité ne s'applique qu'aux propriétaires.
            # Une entreprise a donc un seul propriétaire, mais autant de vendeurs qu'elle veut.
            models.UniqueConstraint(
                fields=["entreprise"],
                condition=Q(role="proprietaire"),
                name="membre_un_seul_proprietaire",
            ),
        ]

    def __str__(self):
        return f"{self.utilisateur} — {self.get_role_display()} ({self.entreprise})"


# ---------------------------------------------------------------------------
# Invitation : jeton secret envoyé à un futur employé
# ---------------------------------------------------------------------------

def expiration_par_defaut():
    """Fonction (et non lambda) pour que Django puisse l'écrire dans les migrations."""
    return timezone.now() + timedelta(days=7)


class Invitation(ModeleEntreprise):
    email = models.EmailField("email de la personne invitée")
    role = models.CharField("rôle proposé", max_length=20, choices=Role.choices, default=Role.VENDEUR)
    # UUID4 : 122 bits aléatoires, impossible à deviner. editable=False : jamais modifiable.
    token = models.UUIDField("jeton", default=uuid.uuid4, unique=True, editable=False)
    invite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # si l'auteur est supprimé, l'invitation reste
        null=True,
        blank=True,
        related_name="invitations_envoyees",
        verbose_name="invité par",
    )
    expire_le = models.DateTimeField("expire le", default=expiration_par_defaut)
    acceptee_le = models.DateTimeField("acceptée le", null=True, blank=True)

    class Meta:
        verbose_name = "invitation"
        verbose_name_plural = "invitations"
        ordering = ["-cree_le"]
        constraints = [
            # Une invitation ne peut JAMAIS donner le rôle de propriétaire.
            models.CheckConstraint(
                condition=Q(role__in=["gerant", "vendeur"]),
                name="invitation_role_autorise",
            ),
            # Une seule invitation en attente par email et par entreprise.
            models.UniqueConstraint(
                fields=["entreprise", "email"],
                condition=Q(acceptee_le__isnull=True),
                name="invitation_unique_en_attente",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def est_valide(self):
        """Utilisable seulement si elle n'a pas encore servi et n'a pas expiré."""
        return self.acceptee_le is None and self.expire_le > timezone.now()

    def __str__(self):
        return f"Invitation de {self.email} ({self.entreprise})"