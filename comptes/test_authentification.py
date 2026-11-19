from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

Utilisateur = get_user_model()
MDP = "Kinshasa!Commerce2026"


class InscriptionTests(TestCase):

    def setUp(self):
        self.url = reverse("comptes:inscription")

    def donnees(self, **modifs):
        donnees = {
            "email": "Nouveau@Exemple.CD",
            "first_name": "Grace",
            "last_name": "Mbuyi",
            "password1": MDP,
            "password2": MDP,
        }
        donnees.update(modifs)
        return donnees

    def test_page_inscription_accessible(self):
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, 200)
        self.assertTemplateUsed(reponse, "comptes/inscription.html")

    def test_inscription_cree_le_compte_et_connecte(self):
        reponse = self.client.post(self.url, self.donnees())
        self.assertRedirects(reponse, reverse("tableau_de_bord:accueil"))
        utilisateur = Utilisateur.objects.get(email="nouveau@exemple.cd")
        self.assertEqual(int(self.client.session["_auth_user_id"]), utilisateur.pk)

    def test_inscription_refuse_email_existant_casse_differente(self):
        Utilisateur.objects.create_user(email="nouveau@exemple.cd", password=MDP)
        reponse = self.client.post(self.url, self.donnees())
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.context["form"].has_error("email"))
        self.assertEqual(Utilisateur.objects.count(), 1)

    def test_inscription_refuse_mots_de_passe_differents(self):
        reponse = self.client.post(self.url, self.donnees(password2="Autre!Chose2026"))
        self.assertTrue(reponse.context["form"].has_error("password2"))
        self.assertFalse(Utilisateur.objects.exists())


class ConnexionTests(TestCase):

    def setUp(self):
        self.url = reverse("comptes:connexion")
        Utilisateur.objects.create_user(email="marie@exemple.cd", password=MDP)

    def test_page_connexion_contient_jeton_csrf(self):
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "csrfmiddlewaretoken")

    def test_connexion_avec_email_en_majuscules(self):
        reponse = self.client.post(self.url, {"username": "MARIE@Exemple.CD", "password": MDP})
        self.assertRedirects(reponse, reverse("tableau_de_bord:accueil"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_connexion_mauvais_mot_de_passe(self):
        reponse = self.client.post(self.url, {"username": "marie@exemple.cd", "password": "faux"})
        self.assertEqual(reponse.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_connexion_sans_jeton_csrf_refusee(self):
        client_strict = Client(enforce_csrf_checks=True)
        reponse = client_strict.post(self.url, {"username": "marie@exemple.cd", "password": MDP})
        self.assertEqual(reponse.status_code, 403)

    def test_utilisateur_connecte_redirige_depuis_connexion(self):
        self.client.force_login(Utilisateur.objects.get(email="marie@exemple.cd"))
        reponse = self.client.get(self.url)
        self.assertRedirects(reponse, reverse("tableau_de_bord:accueil"))


class DeconnexionEtNavigationTests(TestCase):

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(email="paul@exemple.cd", password=MDP)
        self.client.force_login(self.utilisateur)

    def test_deconnexion_en_post(self):
        reponse = self.client.post(reverse("comptes:deconnexion"))
        self.assertRedirects(reponse, reverse("tableau_de_bord:accueil"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_deconnexion_en_get_refusee(self):
        reponse = self.client.get(reverse("comptes:deconnexion"))
        self.assertEqual(reponse.status_code, 405)

    def test_utilisateur_connecte_redirige_depuis_inscription(self):
        reponse = self.client.get(reverse("comptes:inscription"))
        self.assertRedirects(reponse, reverse("tableau_de_bord:accueil"))

    def test_navigation_affiche_email_et_bouton_deconnexion(self):
        reponse = self.client.get(reverse("tableau_de_bord:accueil"))
        self.assertContains(reponse, "paul@exemple.cd")
        self.assertContains(reponse, reverse("comptes:deconnexion"))