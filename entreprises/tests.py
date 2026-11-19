from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Entreprise, Invitation, Membre, Role

Utilisateur = get_user_model()


def creer_utilisateur(email):
    return Utilisateur.objects.create_user(email=email, password="Kinshasa!Commerce2026")


def creer_entreprise(nom="Boutique Mama Grace"):
    return Entreprise.objects.create(nom=nom, taux_usd_cdf=Decimal("2800.00"))


class EntrepriseTests(TestCase):

    def test_str_renvoie_le_nom(self):
        self.assertEqual(str(creer_entreprise()), "Boutique Mama Grace")

    def test_taux_doit_etre_positif(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entreprise.objects.create(nom="Erreur", taux_usd_cdf=Decimal("0"))


class MembreTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()
        self.grace = creer_utilisateur("grace@exemple.cd")

    def test_utilisateur_retrouve_son_entreprise(self):
        Membre.objects.create(entreprise=self.entreprise, utilisateur=self.grace, role=Role.PROPRIETAIRE)
        self.assertEqual(self.grace.membre.entreprise, self.entreprise)

    def test_un_utilisateur_une_seule_entreprise(self):
        autre = creer_entreprise("Quincaillerie Tshala")
        Membre.objects.create(entreprise=self.entreprise, utilisateur=self.grace)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membre.objects.create(entreprise=autre, utilisateur=self.grace)

    def test_un_seul_proprietaire_par_entreprise(self):
        Membre.objects.create(entreprise=self.entreprise, utilisateur=self.grace, role=Role.PROPRIETAIRE)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membre.objects.create(
                    entreprise=self.entreprise,
                    utilisateur=creer_utilisateur("paul@exemple.cd"),
                    role=Role.PROPRIETAIRE,
                )

    def test_plusieurs_vendeurs_autorises(self):
        for email in ("a@exemple.cd", "b@exemple.cd"):
            Membre.objects.create(entreprise=self.entreprise, utilisateur=creer_utilisateur(email), role=Role.VENDEUR)
        self.assertEqual(self.entreprise.membres.count(), 2)


class InvitationTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()

    def inviter(self, email="vendeur@exemple.cd", **kwargs):
        return Invitation.objects.create(entreprise=self.entreprise, email=email, **kwargs)

    def test_jeton_genere_et_unique(self):
        a = self.inviter("a@exemple.cd")
        b = self.inviter("b@exemple.cd")
        self.assertIsInstance(a.token, UUID)
        self.assertNotEqual(a.token, b.token)

    def test_valide_par_defaut_pendant_7_jours(self):
        invitation = self.inviter()
        reste = invitation.expire_le - timezone.now()
        self.assertTrue(invitation.est_valide)
        self.assertTrue(timedelta(days=6, hours=23) < reste <= timedelta(days=7))

    def test_invitation_expiree_invalide(self):
        invitation = self.inviter(expire_le=timezone.now() - timedelta(minutes=1))
        self.assertFalse(invitation.est_valide)

    def test_invitation_deja_acceptee_invalide(self):
        invitation = self.inviter(acceptee_le=timezone.now())
        self.assertFalse(invitation.est_valide)

    def test_role_proprietaire_interdit(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.inviter(role=Role.PROPRIETAIRE)

    def test_email_enregistre_en_minuscules(self):
        self.assertEqual(self.inviter("  Vendeur@EXEMPLE.cd ").email, "vendeur@exemple.cd")

    def test_une_seule_invitation_en_attente_par_email(self):
        self.inviter("vendeur@exemple.cd")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.inviter("VENDEUR@exemple.cd")

    def test_manager_de_filtre_par_entreprise(self):
        autre = creer_entreprise("Quincaillerie Tshala")
        mienne = self.inviter("a@exemple.cd")
        Invitation.objects.create(entreprise=autre, email="b@exemple.cd")
        self.assertQuerySetEqual(Invitation.objects.de(self.entreprise), [mienne])


class EntrepriseAdminTests(TestCase):

    def setUp(self):
        admin = Utilisateur.objects.create_superuser(email="admin@exemple.cd", password="x")
        self.client.force_login(admin)
        self.entreprise = creer_entreprise()

    def test_liste_des_entreprises(self):
        reponse = self.client.get(reverse("admin:entreprises_entreprise_changelist"))
        self.assertContains(reponse, "Boutique Mama Grace")

    def test_fiche_entreprise_avec_membres_et_invitations(self):
        reponse = self.client.get(reverse("admin:entreprises_entreprise_change", args=[self.entreprise.pk]))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "membres-TOTAL_FORMS")
        self.assertContains(reponse, "invitations-TOTAL_FORMS")