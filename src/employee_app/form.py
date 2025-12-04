from django import forms
from .models import RapportDepense


from chantier_app.models import Chantier
from employee_app.models import TypeDepense, Fournisseur


class RapportDepenseForm(forms.ModelForm):
    """Formulaire pour soumettre un rapport depense"""
    class Meta:
        model = RapportDepense
        fields =[
                "type_depense", "materiau_article",
                 "prix_unitaire", "quantité", "fournisseur ", "facture",
                 "note"
                 ]
        
        widget= {
            'materiau_article0':forms.TextInput(attrs={
                'placeholder': 'EX: Tole galvanisée 3mm',
                'class':'form-controle'
            }),
            
            "prix_unitaire":forms.NumberInput(attrs={
                'placeholder': 'Ex: 15000',
                'class':'form-controle'
            }),
            
            "quantité":forms.NumberInput(attrs={
                'placeholder':'Ex: 10',
                'class': 'forms-controle'
            }),
            "note":forms.Textarea(attrs={
                'rows':3,
                'placeholder': 'Ex: Details suplementaire'
            })
        }
        
    def __init__(self, *args, **kwargs):   
        #Récupère l'employee connecté 
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        #Filtre les chantier ou cet employee travaille
        if self.employee:
            self.fields['chantier'].queryset = Chantier.objects.filter(
                equipe_affectee = self.employee
            )
            
        # Trie les types de depenses par ordre d'affichage
        self.fields['type_depense'].queryset = TypeDepense.objects.filter(
            est_actif=True
        ).order_by('ordre_affichage', 'nom')
        
        #Trie les founrnisseur par nom
        self.fields['fournisseur'].queryset = Fournisseur.objects.all().order_by('nom')
        
        # Calcul automatique du total (lecture seule)
        self.fields['total'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                'readonly':True,
                'class':'form-control-plaintext',
                'placeholder': 'calcul automatique'
            }),
            label='Total',
            help_text='Prix unitaire x Quantité'
        )
    
    def clean(self):
        """Validation personalisée"""
        cleaned_data = super().clean()
        
        prix = cleaned_data.get("prix_unitaire")
        quantite = cleaned_data.get("quantité")
        
        #Validation du total 
        if prix and quantite:
            total = prix*quantite
            if total > 10000000:
                self.add_error(None, "Le Total depasse le plafond autorisé (10.000.000 FCFA)")
                
        return cleaned_data
    


class ValidationRapportForm(forms.ModelForm):
    """Formulaire pour Valider/rejeter un rapport"""
    ACTION_CHOICES = [
       ('valide', '✅ Valider la dépense'),
        ('rejete', '❌ Rejeter la dépense'),
        ('modifier', '📝 Demander des modifications'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, 
                               widget=forms.RadioSelect, 
                               required=True, 
                               label='Action'
                            )
    
    commentaire_validation = forms.CharField(
        
        widget = forms.Textarea(attrs={
                                        'rows':3,
                                        'placeholder':'Commentaire (optionnel)',
                                        'class':'form-control'
                                }),
        required=False,
        label='Commentaire'
    )
    
    
    class Meta:
        model= RapportDepense
        fields = [] #pas de champs du modèle, juste l'action
        
    def save(self, commit = True):
        """ Met à jour le status selon l'action"""    
        rapport = super().save(commit=False)
        action = self.cleaned_data.get('action')
        commentaire = self.cleaned_data.get('commentaire_validation', "")
        
        if action == "valide":
            rapport.status = 'valide'
            rapport.note += f"\n[VALIDE] {commentaire}"
            
        elif action == 'rejete':
            rapport.status ="rejete"
            rapport.note = f'\n[REJETE] {commentaire}'
        
        elif action == "modifier":
            rapport.status == "modifier"
            rapport.note = f'\n[A MODIFIER {commentaire}]'
        
        if commit:
            rapport.save()
        
        return rapport
    

class FiltreRapportForm(forms.Form):
    """Formulaire pour filtrer les rapports"""
    date_debut = forms.DateField(
                                    required=False,
                                    widget=forms.DateInput(attrs={'type':'date','class':'form-control'}),
                                    label='date début'
                                )
    
    date_fin = forms.DateField(
                                    required=False,
                                    widget=forms.DateInput(attrs={'type':'date','class':'form-control'}),
                                    label='Date-fin'
    )
    
    status = forms.ChoiceField(
                                    required=False,
                                    choices=[('', "Tous")] + RapportDepense._meta.get_field('status').choices,
                                    widget=forms.Select(attrs={'class':"form-select"}),
                                    label='status'
                                    
    )
    
    type_depense = forms.ModelChoiceField(
                                            required=False,
                                            queryset=TypeDepense.objects.filter(est_actif=True),
                                            widget=forms.Select(attrs={'class':"form-select"}),
                                            label = 'Type de dépense'    
    ) 
    
    chantier = forms.ModelChoiceField(
                                        required=False,
                                        queryset=Chantier.objects.all(),
                                        widget=forms.Select(attrs={'class':'form-select'}),
                                        label='Chantier'
    
    )                                      