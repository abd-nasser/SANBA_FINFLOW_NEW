from django.urls import path
from . import views

app_name="comptable_app"

urlpatterns = [
    
    path("interface-comptable",views.comptable_view, name='comptable-view'),
    path("comptable-approuver/<int:demande_id>/demande", views.comptable_approuve_demande_view, name="comptable-approuver-demande"),
    path("comptable-refuser/<int:demande_id>/demande", views.comptable_refuse_demande_view, name="comptable-refuser-demande"),
    path("comptable-ajouter-fond", views.ajouter_fond, name="comptable-ajouter-fond"),
    path("comptable-rapport-depense-employee", views.list_rapport_depense_view, name="comptable-rapport-depense-employee")
]