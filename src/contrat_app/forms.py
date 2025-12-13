from django import forms
from .models import Contrat

class ContratForm(forms.ModelForm):
    class Meta:
        model = Contrat
        fields = [
                  "chantier","reference_contrat",
                  "date_signature","mode_paiement",
                  "montant_total","acompte_pourcentage",
                  "nombre_tranches","montant_encaisse",
                  "date_du_dernier_paiement","contrat_pdf",
                  'devis_initial', "garantie_mois", 
                  'notes_contractuelles'
                  ]
        widgets = {
            "date_signature":forms.DateInput(attrs={
                "placeholder": "jj/mm/an"
            }),
            
            "date_du_dernier_paiement":forms.DateInput(attrs={
                "placeholder": "jj/mm/an"
            })
            }
       