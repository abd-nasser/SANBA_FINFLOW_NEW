from django.contrib import admin
from .models import TypeDepense, Fournisseur, RapportDepense

@admin.register(TypeDepense)
class AdminTypeDepense(admin.ModelAdmin):
    list_display = ["nom"]


@admin.register(Fournisseur)
class AdminFournisseur(admin.ModelAdmin):
    list_display = ["nom"]
    

@admin.register(RapportDepense)
class AdminRapportDepense(admin.ModelAdmin):
    list_display = ["employee", "type_depense","materiau_article","chantier", "prix_unitaire","quantité","fournisseur","date","total"]
    search_fields=["employee", "materiau_article"]
    list_filter=["type_depense"]
 
