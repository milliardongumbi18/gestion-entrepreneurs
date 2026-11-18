from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UtilisateurManager(BaseUserManager):
    """
    Gestionnaire qui crée les utilisateurs avec l'email comme identifiant.
    Nécessaire car celui de Django attend un champ « username ».
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        # Email entièrement en minuscules : « Jean@Mail.com » = « jean@mail.com »
        email = self.normalize_email(email).lower()
        utilisateur = self.model(email=email, **extra_fields)
        utilisateur.set_password(password)  # hache le mot de passe, jamais en clair
        utilisateur.save(using=self._db)
        return utilisateur

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """
    Utilisateur de l'application. On garde tout ce qu'offre AbstractUser
    (prénom, nom, mot de passe, permissions…) sauf le nom d'utilisateur.
    """

    username = None  # supprime le champ hérité
    email = models.EmailField("adresse email", unique=True)

    USERNAME_FIELD = "email"  # champ utilisé pour se connecter
    REQUIRED_FIELDS = []  # champs demandés en plus par « createsuperuser »

    objects = UtilisateurManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def save(self, *args, **kwargs):
        # Protège aussi les emails modifiés hors du manager (admin, formulaires).
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email