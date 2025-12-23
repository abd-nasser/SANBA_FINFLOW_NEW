from django.urls import path
from . import views

app_name ="directeur_app"

urlpatterns = [
    path("interface-directeur",views.directeur_view, name='directeur-view'),
    path("approuver/<int:demande_id>/demande", views.directeur_approuve_demande_view, name="approuver-demande"),
    path("refuser/<int:demande_id>/demande", views.directeur_refuse_demande_view, name="refuser-demande"),
    path("ajouter-fond", views.ajouter_fond, name="ajouter-fond"),
    path("historique/fonds/", views.historique_ajout_fonf, name='historique-fonds'),
    path("rapport-depense-employee", views.list_rapport_depense_view, name="rapport-depense-employee"),
    path('validation/<int:pk>/rapports', views.ValidationRapportView.as_view(), name="validation-rapports"),
    path("ajouter/fournisseur", views.CreateFournisseurView.as_view(), name="ajouter-fournisseur"),
    path("modifier/rapport/fournisseur/<int:pk>", views.UpdateRapportFournisseurView.as_view(), name="modifier-rapport-fournisseur")
]

