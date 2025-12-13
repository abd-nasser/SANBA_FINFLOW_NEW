from django.contrib import admin
from .models import Contrat

@admin.register(Contrat)
class AdminContrat(admin.ModelAdmin):
    list_display = ['chantier','reference_contrat', 'date_signature', 'mode_paiement', 'montant_total']
