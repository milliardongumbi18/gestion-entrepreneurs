from django.test import TestCase
from django.urls import reverse


class AccueilTests(TestCase):

    def test_accueil_repond_200(self):
        reponse = self.client.get(reverse("tableau_de_bord:accueil"))
        self.assertEqual(reponse.status_code, 200)

    def test_accueil_utilise_le_gabarit_de_base(self):
        reponse = self.client.get(reverse("tableau_de_bord:accueil"))
        self.assertTemplateUsed(reponse, "base.html")
        self.assertTemplateUsed(reponse, "tableau_de_bord/accueil.html")

    def test_page_en_francais_et_adaptee_au_mobile(self):
        reponse = self.client.get(reverse("tableau_de_bord:accueil"))
        self.assertContains(reponse, '<html lang="fr">')
        self.assertContains(reponse, 'name="viewport"')
        self.assertContains(reponse, "css/app.css")