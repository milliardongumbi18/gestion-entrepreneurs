"""
Règles métier des ventes : on ne crée ni n'annule JAMAIS une vente autrement.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from entreprises.models import Devise, Entreprise
from stock.models import TypeMouvement
from stock.services import enregistrer_mouvement

from .models import LigneVente, ModePaiement, StatutVente, Vente

CENTIME = Decimal("0.01")


def convertir(montant, devise_source, devise_cible, taux_usd_cdf):
    """Convertit un montant entre CDF et USD, arrondi au centime (arrondi commercial)."""
    if devise_source == devise_cible:
        resultat = montant
    elif devise_source == Devise.USD:  # USD -> CDF
        resultat = montant * taux_usd_cdf
    else:  # CDF -> USD
        resultat = montant / taux_usd_cdf
    return Decimal(resultat).quantize(CENTIME, rounding=ROUND_HALF_UP)


@transaction.atomic
def enregistrer_vente(entreprise, lignes, *, vendeur=None, client=None, devise=None,
                      mode_paiement=ModePaiement.ESPECES, note=""):
    """
    Crée une vente complète. `lignes` est une liste de (produit, quantité).
    Tout ou rien : si un seul produit manque en stock, AUCUNE écriture n'est conservée.
    """
    # 1. Tout vérifier AVANT d'écrire quoi que ce soit
    if not lignes:
        raise ValueError("Une vente doit contenir au moins un produit.")
    if client is not None and client.entreprise_id != entreprise.pk:
        raise ValueError("Ce client n'appartient pas à cette entreprise.")
    produits_vus = set()
    for produit, quantite in lignes:
        if produit.entreprise_id != entreprise.pk:
            raise ValueError(f"« {produit} » n'appartient pas à cette entreprise.")
        if not produit.actif:
            raise ValueError(f"« {produit} » est archivé et ne peut plus être vendu.")
        if quantite <= 0:
            raise ValueError("Chaque quantité doit être supérieure à zéro.")
        if produit.pk in produits_vus:
            raise ValueError(f"« {produit} » apparaît deux fois : regroupez les quantités.")
        produits_vus.add(produit.pk)

    # 2. Verrouiller l'entreprise pour obtenir un numéro unique, même avec plusieurs vendeurs
    entreprise = Entreprise.objects.select_for_update().get(pk=entreprise.pk)
    entreprise.dernier_numero_vente += 1
    entreprise.save(update_fields=["dernier_numero_vente"])

    devise = devise or entreprise.devise_reference
    taux = entreprise.taux_usd_cdf
    numero = f"V-{timezone.localdate().year}-{entreprise.dernier_numero_vente:05d}"

    vente = Vente.objects.create(
        entreprise=entreprise, numero=numero, client=client, vendeur=vendeur,
        devise=devise, taux_change=taux, mode_paiement=mode_paiement, note=note,
    )

    # 3. Lignes + sorties de stock
    total = total_reference = cout_reference = Decimal("0")
    for produit, quantite in lignes:
        prix_unitaire = convertir(produit.prix_vente, entreprise.devise_reference, devise, taux)
        LigneVente.objects.create(
            vente=vente, produit=produit, quantite=quantite,
            prix_unitaire=prix_unitaire, prix_achat_unitaire=produit.prix_achat,
        )
        # Lève StockInsuffisant si besoin : la transaction annule alors TOUT.
        enregistrer_mouvement(produit, TypeMouvement.VENTE, -quantite, auteur=vendeur, note=numero)
        total += prix_unitaire * quantite
        total_reference += produit.prix_vente * quantite
        cout_reference += produit.prix_achat * quantite

    vente.total = total
    vente.total_reference = total_reference
    vente.cout_reference = cout_reference
    vente.save(update_fields=["total", "total_reference", "cout_reference"])
    return vente


@transaction.atomic
def annuler_vente(vente, *, auteur=None):
    """Annule une vente (sans la supprimer) et remet les produits en stock."""
    vente = Vente.objects.select_for_update().get(pk=vente.pk)
    if vente.statut == StatutVente.ANNULEE:
        raise ValueError(f"La vente {vente.numero} est déjà annulée.")

    for ligne in vente.lignes.select_related("produit"):
        enregistrer_mouvement(
            ligne.produit, TypeMouvement.ANNULATION, ligne.quantite,
            auteur=auteur, note=f"Annulation {vente.numero}",
        )

    vente.statut = StatutVente.ANNULEE
    vente.annulee_le = timezone.now()
    vente.save(update_fields=["statut", "annulee_le"])
    return vente