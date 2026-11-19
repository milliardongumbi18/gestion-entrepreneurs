from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from entreprises.models import Devise, Entreprise
from stock.models import Produit, TypeMouvement
from stock.services import StockInsuffisant, enregistrer_mouvement

from .models import Client, StatutVente, Vente
from .services import annuler_vente, convertir, enregistrer_vente

ANNEE = timezone.localdate().year


def creer_entreprise(nom="Boutique Mama Grace", devise=Devise.CDF):
    return Entreprise.objects.create(nom=nom, devise_reference=devise, taux_usd_cdf=Decimal("2800"))


def creer_produit(entreprise, nom, prix_achat, prix_vente, stock=0, **kwargs):
    produit = Produit.objects.create(
        entreprise=entreprise, nom=nom,
        prix_achat=Decimal(prix_achat), prix_vente=Decimal(prix_vente), **kwargs,
    )
    if stock:
        enregistrer_mouvement(produit, TypeMouvement.ENTREE, stock)
    return produit


class ClientTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()

    def test_str_renvoie_le_nom(self):
        self.assertEqual(str(Client.objects.create(entreprise=self.entreprise, nom="Papa Jean")), "Papa Jean")

    def test_telephone_unique_par_entreprise(self):
        Client.objects.create(entreprise=self.entreprise, nom="A", telephone="+243810000000")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Client.objects.create(entreprise=self.entreprise, nom="B", telephone="+243810000000")


class ConversionTests(TestCase):

    def test_conversions_cdf_usd(self):
        taux = Decimal("2800")
        self.assertEqual(convertir(Decimal("100"), Devise.CDF, Devise.CDF, taux), Decimal("100.00"))
        self.assertEqual(convertir(Decimal("20"), Devise.USD, Devise.CDF, taux), Decimal("56000.00"))
        self.assertEqual(convertir(Decimal("56000"), Devise.CDF, Devise.USD, taux), Decimal("20.00"))


class EnregistrerVenteTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()
        self.riz = creer_produit(self.entreprise, "Riz 25 kg", "45000", "52000", stock=10)
        self.huile = creer_produit(self.entreprise, "Huile 5 L", "15000", "18000", stock=5)

    def test_vente_deduit_le_stock_et_calcule_les_totaux(self):
        vente = enregistrer_vente(self.entreprise, [(self.riz, 2), (self.huile, 1)])
        self.riz.refresh_from_db()
        self.huile.refresh_from_db()
        self.assertEqual((self.riz.quantite_stock, self.huile.quantite_stock), (8, 4))
        self.assertEqual(vente.total, Decimal("122000"))
        self.assertEqual(vente.total_reference, Decimal("122000"))
        self.assertEqual(vente.cout_reference, Decimal("105000"))
        self.assertEqual(vente.marge_reference, Decimal("17000"))

    def test_numerotation_sequentielle(self):
        premiere = enregistrer_vente(self.entreprise, [(self.riz, 1)])
        seconde = enregistrer_vente(self.entreprise, [(self.riz, 1)])
        self.assertEqual(premiere.numero, f"V-{ANNEE}-00001")
        self.assertEqual(seconde.numero, f"V-{ANNEE}-00002")

    def test_prix_copies_au_moment_de_la_vente(self):
        vente = enregistrer_vente(self.entreprise, [(self.riz, 1)])
        self.riz.prix_vente = Decimal("60000")
        self.riz.save()
        self.assertEqual(vente.lignes.get().prix_unitaire, Decimal("52000"))

    def test_vente_en_usd_convertie_au_taux_du_jour(self):
        sac = creer_produit(self.entreprise, "Sac de ciment", "50000", "56000", stock=3)
        vente = enregistrer_vente(self.entreprise, [(sac, 1)], devise=Devise.USD)
        self.assertEqual(vente.total, Decimal("20.00"))
        self.assertEqual(vente.total_reference, Decimal("56000"))
        self.assertEqual(vente.taux_change, Decimal("2800"))

    def test_stock_insuffisant_annule_toute_la_vente(self):
        with self.assertRaises(StockInsuffisant):
            enregistrer_vente(self.entreprise, [(self.riz, 2), (self.huile, 99)])
        self.riz.refresh_from_db()
        self.entreprise.refresh_from_db()
        self.assertEqual(self.riz.quantite_stock, 10)
        self.assertEqual(Vente.objects.count(), 0)
        self.assertEqual(self.entreprise.dernier_numero_vente, 0)

    def test_vente_sans_produit_refusee(self):
        with self.assertRaises(ValueError):
            enregistrer_vente(self.entreprise, [])

    def test_produit_d_une_autre_entreprise_refuse(self):
        autre = creer_entreprise("Dépôt Tshala")
        produit_etranger = creer_produit(autre, "Savon", "500", "800", stock=10)
        with self.assertRaises(ValueError):
            enregistrer_vente(self.entreprise, [(produit_etranger, 1)])

    def test_client_d_une_autre_entreprise_refuse(self):
        client_etranger = Client.objects.create(entreprise=creer_entreprise("Dépôt Tshala"), nom="X")
        with self.assertRaises(ValueError):
            enregistrer_vente(self.entreprise, [(self.riz, 1)], client=client_etranger)

    def test_produit_archive_refuse(self):
        self.riz.actif = False
        self.riz.save()
        with self.assertRaises(ValueError):
            enregistrer_vente(self.entreprise, [(self.riz, 1)])

    def test_meme_produit_deux_fois_refuse(self):
        with self.assertRaises(ValueError):
            enregistrer_vente(self.entreprise, [(self.riz, 1), (self.riz, 2)])


class AnnulerVenteTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()
        self.riz = creer_produit(self.entreprise, "Riz 25 kg", "45000", "52000", stock=10)
        self.vente = enregistrer_vente(self.entreprise, [(self.riz, 3)])

    def test_annulation_remet_le_stock(self):
        annuler_vente(self.vente)
        self.riz.refresh_from_db()
        self.vente.refresh_from_db()
        self.assertEqual(self.riz.quantite_stock, 10)
        self.assertEqual(self.vente.statut, StatutVente.ANNULEE)
        self.assertIsNotNone(self.vente.annulee_le)

    def test_double_annulation_refusee(self):
        annuler_vente(self.vente)
        with self.assertRaises(ValueError):
            annuler_vente(self.vente)


class VenteModeleTests(TestCase):

    def setUp(self):
        self.entreprise = creer_entreprise()

    def test_numero_unique_par_entreprise(self):
        Vente.objects.create(entreprise=self.entreprise, numero="V-2026-00001", devise=Devise.CDF, taux_change=Decimal("2800"))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vente.objects.create(entreprise=self.entreprise, numero="V-2026-00001", devise=Devise.CDF, taux_change=Decimal("2800"))

    def test_filtre_validees(self):
        riz = creer_produit(self.entreprise, "Riz", "45000", "52000", stock=5)
        gardee = enregistrer_vente(self.entreprise, [(riz, 1)])
        annuler_vente(enregistrer_vente(self.entreprise, [(riz, 1)]))
        self.assertQuerySetEqual(Vente.objects.de(self.entreprise).validees(), [gardee])


class VenteAdminTests(TestCase):

    def setUp(self):
        admin = get_user_model().objects.create_superuser(email="admin@exemple.cd", password="x")
        self.client.force_login(admin)
        entreprise = creer_entreprise()
        riz = creer_produit(entreprise, "Riz 25 kg", "45000", "52000", stock=5)
        enregistrer_vente(entreprise, [(riz, 1)])

    def test_liste_des_ventes(self):
        reponse = self.client.get(reverse("admin:ventes_vente_changelist"))
        self.assertContains(reponse, f"V-{ANNEE}-00001")

    def test_ajout_manuel_de_vente_interdit(self):
        reponse = self.client.get(reverse("admin:ventes_vente_add"))
        self.assertEqual(reponse.status_code, 403)