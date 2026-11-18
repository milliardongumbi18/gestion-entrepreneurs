# ÉTAT DU PROJET — Gestion Entrepreneurs

_Dernière mise à jour : 18 novembre 2026_

## Où on en est
- [x] Schéma des modèles validé
- [ ] **1a — Création du projet + GitHub** ← en cours
- [ ] 1b — App `comptes` : utilisateur personnalisé (connexion par email) + tests
- [ ] 1c — Inscription / connexion / déconnexion (vues d'auth intégrées de Django)
- [ ] 1d — Tous les modèles (entreprises, stock, ventes, dépenses, business plan) + admin + tests
- [ ] 1e — Déploiement Render + Neon (service créé à la main, sans Blueprint)

## Stack retenue
- Python 3.14 (pas 3.15 : trop récent, Django 6.1 et certains paquets ne le supportent pas encore officiellement)
- Django 6.1, django-environ, WhiteNoise, gunicorn, psycopg
- SQLite en local, PostgreSQL Neon en production, Render (offre gratuite, sans carte)
- Templates + Tailwind (CLI autonome, sans Node ni CDN) + HTMX + Chart.js (seulement sur le tableau de bord)
- GitHub : milliardongumbi18/gestion-entrepreneurs

## Décisions validées
1. **Un utilisateur = une seule entreprise en V1** (`Membre.utilisateur` en OneToOne). Passage à plusieurs entreprises possible plus tard par simple migration.
2. **Pas de vente à crédit en V1** : une vente est entièrement payée, champ `mode_paiement`.
3. **Bénéfice = CA − coût d'achat des produits vendus − dépenses.** Le réapprovisionnement passe par une entrée de stock, jamais par une dépense.
4. Montants en `DecimalField(max_digits=14, decimal_places=2)`. Chaque vente/dépense garde sa devise, une copie du taux et un `montant_reference` dans la devise de l'entreprise.
5. Isolation multi-entreprise : modèle abstrait `ModeleEntreprise` + `request.entreprise` ; toujours filtrer par entreprise (anti-IDOR).
6. On n'efface jamais une vente (statut « annulée », stock remis) ni un produit vendu (`actif=False`, `PROTECT`).
7. Prix copiés dans `LigneVente` au moment de la vente. Numéro de vente unique par entreprise (`V-2026-00042`).
8. Business plan : champs texte explicites par section + `PrevisionAnnuelle` (années 1 à 3).

## Apps
`comptes`, `entreprises`, `stock`, `ventes`, `depenses`, `businessplan`, `tableau_de_bord` (sans modèle).

## Méthode de travail (résumé)
- Claude code tout et explique ; pas d'exercices. Moi : j'applique, teste, déploie, signale les erreurs.
- Rythme « molo molo », étapes découpées (1a, 1b…). Hors périmètre ou délai rallongé → le dire avant de coder.
- Format de chaque étape : 🎯 Objectif + branche → 🗺 Fichiers → 📁 Code complet avec chemin → ▶️ Commandes PowerShell → ✅ Vérification (check, tests avec nombre attendu, navigateur) → 🔀 Commit / PR / déploiement / nettoyage → 📌 À retenir → ⏭️ Prochaine étape.
- Contraintes : aucun service exigeant une carte bancaire ; utilisateurs sur téléphone avec données mobiles chères.
