from django.contrib import admin
from .models import DemandeDecaissement

@admin.register(DemandeDecaissement)
class AdminDemandeDecaissement(admin.ModelAdmin):
    list_display =["nom", "montant", "chantier", "motif", "status", "approuve_par", "date_demande","date_approbation", "date_decaissement"]
