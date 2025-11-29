from django.urls import path
from . import views

app_name = 'client_app'

urlpatterns = [
#URLs pour la gestion des clients
    path("client/", views.ClientListView.as_view(), name="liste-client"),
    path("ajouter-client/", views.ClientCreateView.as_view(), name="ajouter-client"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="detail-client"),
    path("<int:pk>/modifier-client/", views.ClientUpdateView.as_view(), name="modifier-client"),
    path("<int:pk>/supprimer-client/", views.ClientDeleteView.as_view(), name="supprimer-client"),
         ]

