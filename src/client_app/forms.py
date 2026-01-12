from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            
            'type_client', 'raison_sociale', 'nom', 'prenom',
            'telephone', 'telephone_secondaire', 'email', 
            'adresse', 'ville', 'quartier', 'secteur_activite',
            'source_client', 'potentiel_client', 'notes_internes'
        ]
        
        #Personalisations des labels
        labels = {
            'type_client': "Type de client",
            'raison_sociale': "Raison sociale",
            'nom': "Nom",
            'prenom': "Prénom",
            'telephone': "Téléphone principal",
            'telephone_secondaire': "Téléphone secondaire",
            'email': "Adresse e-mail",
            'adresse': "Adresse physique",
            'ville': "Ville",
            'quartier': "Quartier",
            'secteur_activite': "Secteur d'activité",
            'source_client': "Source du client",
            'potentiel_client': "Potentiel du client",
            'notes_internes': "Notes internes",
        }
        
        #textarea pour les champs longs
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3, "class": "input input-bordered w-full"}),
            'notes_internes': forms.Textarea(attrs={'rows': 4, "class": "input input-bordered w-full"}),
        }  
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            
        # Personnalisation des champs si nécessaire
        self.fields['email'].required = False
        self.fields['telephone_secondaire'].required = False
            
      # placeholders pour guider l'utilisateur
        self.fields['type_client'].widget.attrs.update({"class": "select select-bordered"})
        self.fields['nom'].widget.attrs.update({"class": "input input-bordered w-full", "placeholder": "Ex: Ouedraogo"})
        self.fields["prenom"].widget.attrs.update({"class": "input input-bordered w-full", "placeholder": "Ex: Rachide"})
        self.fields['telephone'].widget.attrs.update({"class": "input input-bordered w-full", 'placeholder': 'Ex: +226 70 12 34 56'})
        self.fields['telephone_secondaire'].widget.attrs.update({"class": "input input-bordered w-full", 'placeholder': 'Ex: +226 70 12 34 56'})
        self.fields['email'].widget.attrs.update({"class": "input input-bordered w-full", 'placeholder': 'Ex: client@email.com'})
        self.fields['ville'].widget.attrs.update({"class": "input input-bordered w-full", 'placeholder': 'Ex: Ouagadougou'})
        self.fields['quartier'].widget.attrs.update({"class": "input input-bordered w-full", 'placeholder': 'Ex: Tampouy'})
        self.fields['secteur_activite'].widget.attrs.update({"class": "select select-bordered"})
        self.fields['source_client'].widget.attrs.update({"class": "select select-bordered"})
      
       
        
    def clean_telephone(self):
        """Validation du numéro de telephone """
        telephone = self.cleaned_data.get("telephone")
        if telephone:
            #nettoyage du numero
            telephone = ''.join(filter(str.isdigit, telephone))
        if len(telephone) < 8:
            raise forms.ValidationError("Numéro de téléphone invalide")
        return telephone
         
    def clean(self):
        """Verification croisée"""
        cleaned_data = super().clean()
        type_client = cleaned_data.get("type_client")
        raison_sociale = cleaned_data.get("raison_sociale")
            
        #si c'est une entreprise, la raison sociale est obligatoire
        if type_client == 'entreprise' and not raison_sociale:
            self.add_error('raison_sociale', "La raison sociale est obligatoire pour les entreprises.")
        return cleaned_data
                
                
