from django.urls import path

from .views import AccueilView

app_name = "tableau_de_bord"  # espace de noms : {% url 'tableau_de_bord:accueil' %}

urlpatterns = [
    path("", AccueilView.as_view(), name="accueil"),
]