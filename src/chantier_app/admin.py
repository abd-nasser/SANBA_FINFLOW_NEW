from django.contrib import admin
from .models import Chantier

@admin.register(Chantier)
class AdminChantier(admin.ModelAdmin):
    list_display=["nom_chantier", "reference", "status_chantier", "date_debut_prevue", "date_fin_prevue"]
