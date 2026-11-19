# ÉTAT DU PROJET — Gestion Entrepreneurs

_Dernière mise à jour : 19 novembre 2026_

## Où on en est
- [x] Schéma des modèles validé
- [x] 1a — Création du projet + GitHub (dossier local `C:\Users\Blaise\gestion-entrepreneurs`)
- [x] 1b — App `comptes` : utilisateur personnalisé (connexion par email) + 10 tests
- [x] 1c — Tailwind v4.3.5 (CLI autonome) + gabarit de base mobile + page d'accueil (app `tableau_de_bord`) + .gitattributes — 13 tests
- [x] 1d — Inscription / connexion / déconnexion — 26 tests
- [ ] **1e — Déploiement Render (Frankfurt, Free) + Neon (Frankfurt, Free)** ← en cours (branche `feature/deploiement-render`)
- [ ] 1f et suivantes — Modèles entreprises, stock, ventes, dépenses, business plan + admin + tests

Note : une copie de ce fichier existe aussi dans le dépôt (`docs/ETAT_DU_PROJET.md`).

## Déploiement
- Build : `bash build.sh` (pip install, collectstatic, migrate). Start : `gunicorn config.wsgi:application`.
- Variables Render : PYTHON_VERSION, SECRET_KEY (différente du local), DEBUG=False, DATABASE_URL (Neon). RENDER_EXTERNAL_HOSTNAME est fourni par Render.
- Pas de Shell sur l'offre gratuite Render : commandes ponctuelles (createsuperuser) lancées depuis le PC avec DATABASE_URL de Neon saisie via Read-Host.
- Source Tailwind déplacée dans `tailwind/entree.css` (hors de `static/`) : sinon collectstatic en production échoue sur `@import "tailwindcss"`.

## Points ouverts (à décider plus tard)
- Limitation des tentatives de connexion (anti force brute) : pas encore en place.
- Réinitialisation du mot de passe par email : nécessite un service d'envoi d'emails gratuit sans carte.

## Stack retenue
- Python 3.14 (pas 3.15 : trop récent, Django 6.1 et certains paquets ne le supportent pas encore officiellement)
- Django 6.1.3, django-environ, WhiteNoise, gunicorn, psycopg
- SQLite en local, PostgreSQL Neon en production, Render (offre gratuite, sans carte)
- Templates + Tailwind v4 (exécutable autonome `tailwindcss.exe`, non commité ; CSS compilé et minifié `static/css/app.css` commité) + HTMX + Chart.js (seulement sur le tableau de bord)
- Fins de ligne : LF partout via `.gitattributes`
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
9. Utilisateur : `AbstractUser` sans `username`, connexion par email, email stocké en minuscules (unicité insensible à la casse).
10. Authentification : vues intégrées de Django (`LoginView`, `LogoutView` en POST uniquement), inscription maison avec connexion automatique. URLs sous `/comptes/`.

## Apps
`comptes`, `entreprises`, `stock`, `ventes`, `depenses`, `businessplan`, `tableau_de_bord` (sans modèle).
Règle : toujours `startapp` AVANT d'ajouter l'app dans `INSTALLED_APPS`.

## Méthode de travail (résumé)
- Claude code tout et explique ; pas d'exercices. Moi : j'applique, teste, déploie, signale les erreurs.
- Rythme « molo molo », étapes découpées (1a, 1b…). Hors périmètre ou délai rallongé → le dire avant de coder.
- Format de chaque étape : 🎯 Objectif + branche → 🗺 Fichiers → 📁 Code complet avec chemin → ▶️ Commandes PowerShell → ✅ Vérification (check, tests avec nombre attendu, navigateur) → 🔀 Commit / PR / déploiement / nettoyage → 📌 À retenir → ⏭️ Prochaine étape.
- Contraintes : aucun service exigeant une carte bancaire ; utilisateurs sur téléphone avec données mobiles chères.
- Astuces Windows : afficher les extensions de fichiers ; Enregistrement automatique dans VS Code ; coller les commandes une par une.
