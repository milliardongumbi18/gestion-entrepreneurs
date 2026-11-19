from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccueilTests(TestCase):

    def setUp(self):
        self.url = reverse("tableau_de_bord:accueil")

    def test_accueil_repond_200(self):
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, 200)

    def test_accueil_utilise_le_gabarit_de_base(self):
        reponse = self.client.get(self.url)
        self.assertTemplateUsed(reponse, "base.html")
        self.assertTemplateUsed(reponse, "tableau_de_bord/accueil.html")

    def test_page_en_francais_et_adaptee_au_mobile(self):
        reponse = self.client.get(self.url)
        self.assertContains(reponse, '<html lang="fr">')
        self.assertContains(reponse, 'name="viewport"')
        self.assertContains(reponse, "css/app.css")

    def test_visiteur_voit_l_appel_a_l_inscription(self):
        reponse = self.client.get(self.url)
        self.assertContains(reponse, "Commencer gratuitement")

    def test_utilisateur_connecte_voit_un_accueil_personnalise(self):
        utilisateur = get_user_model().objects.create_user(
            email="grace@exemple.cd", password="Kinshasa!Commerce2026", first_name="Grace"
        )
        self.client.force_login(utilisateur)
        reponse = self.client.get(self.url)
        self.assertContains(reponse, "Bonjour Grace")
        self.assertNotContains(reponse, "Commencer gratuitement")