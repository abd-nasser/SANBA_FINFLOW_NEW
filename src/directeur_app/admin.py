from django.contrib import admin
from .models import FondDisponible, Historique_dajout_fond

@admin.register(FondDisponible)
class AdminFondDisponible(admin.ModelAdmin):
    list_display = ["montant", "date_ajout"]
    
@admin.register(Historique_dajout_fond)
class AdminHistorique_dajout_fond(admin.ModelAdmin):
    list_display = ["nom","montant", "date_ajout"]
