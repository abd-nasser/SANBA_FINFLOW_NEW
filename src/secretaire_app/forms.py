from django import forms
from .models import DemandeDecaissement


class DemandeDecaissementForm(forms.ModelForm):
    class Meta:
        model = DemandeDecaissement
        fields = "__all__"
        exclude = ["status","approuve_par","date_approbation","date","date_decaissement","decaisse"]
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs )
        self.fields["chantier"].required= False
        self.fields["motif"].required=True
        self.fields["reference_demande"].required=True
        
        
    