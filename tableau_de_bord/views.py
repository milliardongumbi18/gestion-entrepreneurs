from django.views.generic import TemplateView


class AccueilView(TemplateView):
    """Page d'accueil publique. Elle deviendra le tableau de bord après connexion."""

    template_name = "tableau_de_bord/accueil.html"