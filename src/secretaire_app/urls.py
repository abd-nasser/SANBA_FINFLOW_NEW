from django.urls import path
from . import views

app_name = "secretaire_app"

urlpatterns = [
    path("interface-secretaire", views.demande_decaissement_view, name="secretaire-view"),
    path("valider-decaissement/<int:decaissement_id>", views.valider_decaissement_view, name="valider-decaissement"),
    path("hist-demande-decaisse", views.HistoriqueDemandeView.as_view(), name="hist-demande-decaisse"),
    path("filter-demande-decaisse", views.filter_demande_decaisse, name="filter-demande-decaisse")
]
