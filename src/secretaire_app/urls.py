from django.urls import path
from . import views

app_name = "secretaire_app"

urlpatterns = [
    path("interface-secretaire", views.demande_decaissement_view, name="secretaire-view"),
    path("valider-decaissement/<int:decaissement_id>", views.valider_decaissement_view, name="valider-decaissement")
]
