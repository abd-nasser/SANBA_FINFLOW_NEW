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
    
    #Gestion des status de chantiers
    path('chantier/<int:chantier_id>/commencer/',views.commencer_chantier_view, name='commencer-chantier'),
    path('chantier/<int:chantier_id>/terminer/',views.terminer_chantier_view, name='terminer-chantier'),
    path('chantier/<int:chantier_id>/suspendre/',views.suspendre_chantier_view, name='suspendre-chantier'),
    path('chantier/<int:chantier_id>/planifier/', views.planifier_chantier_view, name='planifier-chantier'),
    path('chantier/<int:chantier_id>/annuler/', views.annuler_chantier_view, name='annuler-chantier'),
    
    #URL pour ouvrir le modal pour le changement de status
    path('chantier/<int:chantier_id>/status-modal/',views.get_status_modal, name='status-modal'),

    
]