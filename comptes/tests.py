from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Utilisateur


class UtilisateurModeleTests(TestCase):
    """Tests du modèle et de son gestionnaire."""

    def test_get_user_model_renvoie_utilisateur(self):
        self.assertIs(get_user_model(), Utilisateur)

    def test_creer_utilisateur_normalise_email(self):
        u = Utilisateur.objects.create_user(email="  Jean.Kabila@GMAIL.com ", password="MotDePasse!2026")
        self.assertEqual(u.email, "jean.kabila@gmail.com")
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.is_active)

    def test_mot_de_passe_hache(self):
        u = Utilisateur.objects.create_user(email="a@exemple.cd", password="MotDePasse!2026")
        self.assertNotEqual(u.password, "MotDePasse!2026")
        self.assertTrue(u.check_password("MotDePasse!2026"))

    def test_email_obligatoire(self):
        with self.assertRaises(ValueError):
            Utilisateur.objects.create_user(email="", password="MotDePasse!2026")

    def test_email_unique_insensible_a_la_casse(self):
        Utilisateur.objects.create_user(email="marie@exemple.cd", password="x")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Utilisateur.objects.create_user(email="MARIE@exemple.cd", password="y")

    def test_creer_superutilisateur(self):
        admin = Utilisateur.objects.create_superuser(email="admin@exemple.cd", password="x")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_superutilisateur_refuse_sans_droits(self):
        with self.assertRaises(ValueError):
            Utilisateur.objects.create_superuser(email="b@exemple.cd", password="x", is_staff=False)
        with self.assertRaises(ValueError):
            Utilisateur.objects.create_superuser(email="c@exemple.cd", password="x", is_superuser=False)

    def test_str_renvoie_email(self):
        u = Utilisateur.objects.create_user(email="paul@exemple.cd", password="x")
        self.assertEqual(str(u), "paul@exemple.cd")


class UtilisateurAdminTests(TestCase):
    """Vérifie que l'admin fonctionne sans le champ « username »."""

    def setUp(self):
        self.admin = Utilisateur.objects.create_superuser(email="admin@exemple.cd", password="x")
        self.client.force_login(self.admin)

    def test_admin_liste_utilisateurs(self):
        reponse = self.client.get(reverse("admin:comptes_utilisateur_changelist"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "admin@exemple.cd")

    def test_admin_formulaire_ajout(self):
        reponse = self.client.get(reverse("admin:comptes_utilisateur_add"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'name="email"')
        self.assertNotContains(reponse, 'name="username"')