from django import forms
from .models import DemandeDecaissement


class DemandeDecaissementForm(forms.ModelForm):
    class Meta:
        model = DemandeDecaissement
        fields = "__all__"
        exclude = ["status","approuve_par","date_approbation","date","date_decaissement","decaisse"]
        
      # Ajoutez ceci dans vos widgets si le champ chantier est un ModelChoiceField
        widgets={
            "demandeur": forms.Select(attrs={"class": "input input-bordered"}),
            "montant": forms.NumberInput(attrs={"class": "input input-bordered", "placeholder": "Ex: 100000"}),
            "motif": forms.Textarea(attrs={'rows': 3, "class": "textarea textarea-bordered"}),
            "reference_demande": forms.TextInput(attrs={"class": "input input-bordered", "placeholder": "Ex: dmd_01"}),
            "chantier": forms.Select(attrs={"class": "select select-bordered"})  # Ajout important pour DaisyUI
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs )
        self.fields["chantier"].required= False
        self.fields["motif"].required=True
        self.fields["reference_demande"].required=True
        
        
    