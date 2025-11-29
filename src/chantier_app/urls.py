from django.urls import path
from . import views

app_name = 'chantier_app'

urlpatterns = [
    
    #URLs pour la gestion des chantiers
    path("chantier/", views.ChantierListeView.as_view(), name="liste-chantier"),
    path("ajouter-chantier/", views.ChantierCreateView.as_view(), name="ajouter-chantier"),
    path("<int:pk>/detail-chantier/", views.ChantierDetailView.as_view(), name="detail-chantier"),
    path("<int:pk>/modifier-chantier/", views.ChantierUpdateView.as_view(), name="modifier-chantier"),
    path("<int:pk>/supprimer-chantier/", views.ChantierDeleteView.as_view(), name="supprimer-chantier"),
    
    
#URL pour le filtrage HTMX des chantiers    
    path('filter-chantiers', views.filter_chantiers_htmx, name="filter-chantiers"),
    
]