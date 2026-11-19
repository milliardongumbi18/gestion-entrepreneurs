# Gestion Entrepreneurs

Application web Django pour petits commerces et jeunes entrepreneurs (Kinshasa, RDC) :
stock, ventes, dépenses, tableau de bord, factures PDF et assistant de business plan.

## Installation locale (Windows)

    py -3.14 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env   # puis renseigner SECRET_KEY
    python manage.py migrate
    python manage.py runserver

## CSS (Tailwind v4, exécutable autonome)

Télécharger `tailwindcss-windows-x64.exe` depuis les releases GitHub de Tailwind,
le renommer `tailwindcss.exe` à la racine, puis :

    # Pendant le développement
    .\tailwindcss.exe -i tailwind\entree.css -o static\css\app.css --watch
    # Avant chaque commit
    .\tailwindcss.exe -i tailwind\entree.css -o static\css\app.css --minify

## Déploiement

Render (Web Service gratuit) + Neon (PostgreSQL gratuit).
Build : `bash build.sh` — Start : `gunicorn config.wsgi:application`.