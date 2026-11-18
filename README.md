# Gestion Entrepreneurs

Application web Django pour petits commerces et jeunes entrepreneurs (Kinshasa, RDC) :
stock, ventes, dépenses, tableau de bord, factures PDF et assistant de business plan.

## Installation locale (Windows)

    py -3.14 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env   # puis renseigner SECRET_KEY
    python manage.py runserver