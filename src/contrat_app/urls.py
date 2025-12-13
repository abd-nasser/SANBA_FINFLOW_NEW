from django.urls import path
from . import views

app_name = "contrat_app"

urlpatterns = [
    path("contrats/", views.ContratView.as_view(), name='liste-contrats'),
    path("nouveau/contrat", views.createContratView.as_view(), name='ajouter-contrat'),
    path("modifier/<int:pk>/contrat", views.ContratUpdateView.as_view(), name='modifier-contrat'),
    path("detail/<int:pk>/contrat", views.ContratDetaiView.as_view(), name='detail-contrat'),
    path("supprimer/<int:pk>/contrat", views.ContratDeleteView.as_view(), name='supprimer-contrat'),
    path('enregister/<int:contrat_id>/nouveau-paiement/', views.enregister_paiement_view, name="nouveau-paiement")
]
