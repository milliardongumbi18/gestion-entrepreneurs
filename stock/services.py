"""
Règles métier du stock.
Le stock d'un produit ne doit JAMAIS être modifié directement :
toujours passer par enregistrer_mouvement(), qui garde l'historique.
"""
from django.db import transaction
from django.db.models import F

from .models import MouvementStock, Produit, TypeMouvement


class StockInsuffisant(Exception):
    """Une sortie demande plus que la quantité disponible."""


# Sens attendu pour chaque type : +1 (le stock monte), -1 (il baisse), None (les deux possibles)
SENS_ATTENDU = {
    TypeMouvement.ENTREE: 1,
    TypeMouvement.ANNULATION: 1,
    TypeMouvement.VENTE: -1,
    TypeMouvement.AJUSTEMENT: None,
}


@transaction.atomic
def enregistrer_mouvement(produit, type_mouvement, quantite, *, auteur=None, cout_unitaire=None, note=""):
    """
    Modifie le stock ET enregistre le mouvement, en une seule transaction :
    soit les deux réussissent, soit rien n'est enregistré.
    """
    if quantite == 0:
        raise ValueError("La quantité d'un mouvement ne peut pas être nulle.")

    sens = SENS_ATTENDU[type_mouvement]
    if sens is not None and (quantite > 0) != (sens > 0):
        raise ValueError("Le signe de la quantité ne correspond pas au type de mouvement.")

    lignes = Produit.objects.filter(pk=produit.pk)
    if quantite < 0:
        # Mise à jour conditionnelle : elle ne s'applique que si le stock suffit.
        lignes = lignes.filter(quantite_stock__gte=-quantite)

    # F() fait le calcul DANS la base (UPDATE ... SET quantite_stock = quantite_stock + n) :
    # deux vendeurs qui vendent en même temps ne peuvent pas s'écraser mutuellement.
    if lignes.update(quantite_stock=F("quantite_stock") + quantite) == 0:
        raise StockInsuffisant(f"Stock insuffisant pour « {produit.nom} ».")

    mouvement = MouvementStock.objects.create(
        produit=produit,
        type=type_mouvement,
        quantite=quantite,
        cout_unitaire=cout_unitaire,
        note=note,
        auteur=auteur,
    )
    produit.refresh_from_db(fields=["quantite_stock"])
    return mouvement