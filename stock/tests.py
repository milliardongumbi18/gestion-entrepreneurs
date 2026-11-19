from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from entreprises.models import Entreprise

from .models import MouvementStock, Produit, TypeMouvement
from .services import StockInsuffisant, enregistrer_mouvement


def creer_entreprise(nom="Boutique Mama Grace"):
    return Entreprise.objects.create(nom=nom, taux_usd_cdf=Decimal("2800"))


def creer_produit(entreprise, nom="Riz 25 kg", **kwargs):
    valeurs = {"prix_achat": Decimal("45000"), "prix_vente": Decimal("52000")}
    valeurs.update(kwargs)
    return Produit.objects.create(entreprise=entreprise, nom=nom, **valeurs)


class ProduitTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()

    def test_str_renvoie_le_nom(self):
        self.assertEqual(str(creer_produit(self.entreprise)), "Riz 25 kg")

    def test_marge_unitaire(self):
        self.assertEqual(creer_produit(self.entreprise).marge_unitaire, Decimal("7000"))

    def test_nom_unique_par_entreprise_sans_tenir_compte_de_la_casse(self):
        creer_produit(self.entreprise, "Riz 25 kg")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                creer_produit(self.entreprise, "RIZ 25 KG")

    def test_meme_nom_autorise_dans_deux_entreprises(self):
        creer_produit(self.entreprise, "Riz 25 kg")
        creer_produit(creer_entreprise("Dépôt Tshala"), "Riz 25 kg")
        self.assertEqual(Produit.objects.count(), 2)

    def test_prix_negatif_refuse(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                creer_produit(self.entreprise, prix_vente=Decimal("-1"))

    def test_propriete_en_alerte(self):
        produit = creer_produit(self.entreprise, quantite_stock=5, seuil_alerte=5)
        self.assertTrue(produit.en_alerte)

    def test_filtres_actifs_et_en_alerte(self):
        bas = creer_produit(self.entreprise, "Huile 5 L", quantite_stock=2, seuil_alerte=5)
        creer_produit(self.entreprise, "Sucre 1 kg", quantite_stock=50, seuil_alerte=5)
        creer_produit(self.entreprise, "Ancien produit", quantite_stock=0, actif=False)
        self.assertQuerySetEqual(Produit.objects.de(self.entreprise).en_alerte(), [bas])

    def test_stock_jamais_negatif_en_base(self):
        produit = creer_produit(self.entreprise)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Produit.objects.filter(pk=produit.pk).update(quantite_stock=-1)


class MouvementStockTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()
        self.produit = creer_produit(self.entreprise)

    def test_entree_augmente_le_stock_et_garde_une_trace(self):
        mouvement = enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 20, cout_unitaire=Decimal("45000"))
        self.assertEqual(self.produit.quantite_stock, 20)
        self.assertEqual(mouvement.quantite, 20)
        self.assertEqual(self.produit.mouvements.count(), 1)

    def test_vente_diminue_le_stock(self):
        enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 10)
        enregistrer_mouvement(self.produit, TypeMouvement.VENTE, -3)
        self.assertEqual(self.produit.quantite_stock, 7)

    def test_stock_insuffisant_ne_modifie_rien(self):
        enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 2)
        with self.assertRaises(StockInsuffisant):
            enregistrer_mouvement(self.produit, TypeMouvement.VENTE, -5)
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.quantite_stock, 2)
        self.assertEqual(self.produit.mouvements.count(), 1)

    def test_quantite_nulle_ou_signe_incoherent_refuses(self):
        with self.assertRaises(ValueError):
            enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 0)
        with self.assertRaises(ValueError):
            enregistrer_mouvement(self.produit, TypeMouvement.VENTE, 3)

    def test_mouvement_prend_l_entreprise_du_produit(self):
        mouvement = enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 1)
        self.assertEqual(mouvement.entreprise, self.entreprise)

    def test_mouvement_avec_une_autre_entreprise_refuse(self):
        autre = creer_entreprise("Dépôt Tshala")
        with self.assertRaises(ValueError):
            MouvementStock.objects.create(
                entreprise=autre, produit=self.produit, type=TypeMouvement.ENTREE, quantite=1
            )

    def test_produit_avec_historique_ne_peut_pas_etre_supprime(self):
        enregistrer_mouvement(self.produit, TypeMouvement.ENTREE, 1)
        with self.assertRaises(ProtectedError):
            self.produit.delete()


class StockAdminTests(TestCase):

    def setUp(self):
        admin = get_user_model().objects.create_superuser(email="admin@exemple.cd", password="x")
        self.client.force_login(admin)
        creer_produit(creer_entreprise())

    def test_liste_des_produits(self):
        reponse = self.client.get(reverse("admin:stock_produit_changelist"))
        self.assertContains(reponse, "Riz 25 kg")

    def test_ajout_manuel_de_mouvement_interdit(self):
        reponse = self.client.get(reverse("admin:stock_mouvementstock_add"))
        self.assertEqual(reponse.status_code, 403)