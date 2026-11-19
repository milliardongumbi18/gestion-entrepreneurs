#!/usr/bin/env bash
# Script exécuté par Render à chaque déploiement.
# set -o errexit : on s'arrête à la première erreur (pas de déploiement à moitié fait).
set -o errexit

pip install -r requirements.txt

# Copie et compresse les fichiers statiques dans staticfiles/ (servis par WhiteNoise)
python manage.py collectstatic --no-input

# Applique les migrations sur la base Neon
python manage.py migrate --no-input