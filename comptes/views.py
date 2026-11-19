from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import ConnexionForm, InscriptionForm


class InscriptionView(FormView):
    """Crée le compte puis connecte directement l'utilisateur."""

    template_name = "comptes/inscription.html"
    form_class = InscriptionForm
    success_url = reverse_lazy("tableau_de_bord:accueil")

    def dispatch(self, request, *args, **kwargs):
        # Un utilisateur déjà connecté n'a rien à faire ici.
        if request.user.is_authenticated:
            return redirect("tableau_de_bord:accueil")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        utilisateur = form.save()
        login(self.request, utilisateur)
        messages.success(self.request, "Bienvenue ! Votre compte a été créé.")
        return super().form_valid(form)


class ConnexionView(LoginView):
    """Vue de connexion de Django, avec notre formulaire et notre template."""

    template_name = "comptes/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Vous êtes connecté.")
        return super().form_valid(form)


class DeconnexionView(LogoutView):
    """Déconnexion : uniquement en POST (protégée par le jeton CSRF)."""

    def post(self, request, *args, **kwargs):
        reponse = super().post(request, *args, **kwargs)
        messages.info(request, "Vous êtes déconnecté.")
        return reponse