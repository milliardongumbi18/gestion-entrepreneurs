from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("comptes/", include("comptes.urls")),
    path("", include("tableau_de_bord.urls")),
]