from django import forms
from .models import RapportDepense
from django.core.mail import send_mail
from django.conf import settings
import logging
from chantier_app.models import Chantier
from employee_app.models import TypeDepense, Fournisseur

logger = logging.getLogger(__name__)
class RapportDepenseForm(forms.ModelForm):
    """Formulaire pour soumettre un rapport depense"""
    
    class Meta:
        model = RapportDepense
        fields =[
                "demande_decaissement",
                "type_depense", "materiau_article",
                 "prix_unitaire", "quantité","fournisseur_not_db", "fournisseur", "facture",
                 "note", "chantier","date_depense",
                 ]
        
        widgets= {
            'materiau_article':forms.TextInput(attrs={
                'placeholder': 'EX: Tole galvanisée 3mm',
                'class':'form-controle'
            }),
            
            "prix_unitaire":forms.NumberInput(attrs={
                'placeholder': 'Ex: 15000',
                'class': 'form-control'
            }),
            
            "quantité":forms.NumberInput(attrs={
                'placeholder':'Ex: 10',
                'class': 'forms-controle'
            }),
            
            "fournisseur_not_db":forms.TextInput(attrs={
                'placeholder':"  Si nouveau founisseur ",
                'class': 'forms-controle'
            }),
            
            
            'facture': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*,.pdf,.jpg,.jpeg,.png'}),
            
            "note":forms.Textarea(attrs={
                'rows':3,
                'placeholder': 'Ex: Details suplementaire'
            }),
            "date_depense":forms.DateInput(attrs={
                'type': 'date',
                'class':'forms-controle'
            })
        }
        
    def __init__(self, *args, **kwargs):   
        #Récupère l'employee connecté 
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        self.fields['type_depense'].required=True
        self.fields['prix_unitaire'].required=True
        self.fields['quantité'].required=True
        self.fields['note'].required=True
        self.fields['chantier'].required=False
        self.fields['demande_decaissement'].required=True
        
        # Personnaliser le champ facture
        self.fields['facture'].required = False
        self.fields['facture'].help_text = "Téléchargez la facture (image ou PDF)"
        self.fields['facture'].label = "📄 Facture"
        
        
        # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300"
        
        for field_name, field in self.fields.items():
            # Classes de base
            field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-full"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-full"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
            

        
        # AJOUTE CE FILTRE POUR LES DEMANDES :
        if self.employee:
            # Récupère les demandes approuvées de cet employé des dernières 48h
            from datetime import timedelta
            from django.utils import timezone
            from secretaire_app.models import DemandeDecaissement
            
            date_limite = timezone.now() - timedelta(hours=72)
            
            self.fields['demande_decaissement'].queryset = DemandeDecaissement.objects.filter(
                demandeur=self.employee,# ou le champ qui lie à l'employé
                decaisse = True,
                date_decaissement__gte=date_limite
            ).order_by('-date_decaissement')
            
        
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
                               widget=forms.RadioSelect(attrs={
                                   "class":"radio radio-secondary"}), 
                               required=True, 
                               label='Action'
                            )
    
    commentaire_validation = forms.CharField(
        
        widget = forms.Textarea(attrs={
                                        'rows':3,
                                        'placeholder':'Commentaire (optionnel)',
                                        'class':'textarea textarea-bordered'
                                }),
        required=False,
        label='Commentaire'
    )
    
    
    class Meta:
        model= RapportDepense
        fields = [] #pas de champs du modèle, juste l'action
        
    def save(self, commit=True):
        """ Met à jour le status selon l'action"""    
        rapport = super().save(commit=False)
        action = self.cleaned_data.get('action')
        commentaire = self.cleaned_data.get('commentaire_validation', "")
        
        if action == "valide":
            rapport.status = 'valide'
            rapport.note += f"\n[VALIDE] {commentaire}"
            try:
                # Envoi d'un email de notification à l'employé
                send_mail(
                    subject='✅ Votre rapport de dépense a été validé',
                    message=f"""
                    Bonjour {rapport.employee.username},
                    
                    Votre rapport de dépense concernant "{rapport.materiau_article}" 
                    pour un montant de {rapport.prix_unitaire * rapport.quantité} FCFA a été validé.
                    
                    Merci pour votre diligence.
                    
                    Cordialement,
                    L'équipe de gestion des dépenses
                    """,
                    from_email="sanbasystemegestion@gmail.com",
                    recipient_list=[rapport.employee.email, "nasserdevtest@gmail.com"],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur envoi mail validation rapport {e}")
                
            
        elif action == 'rejete':
            rapport.status ="rejete"
            rapport.note = f'\n[REJETE] {commentaire}'
            try:
                # Envoi d'un email de notification à l'employé
                send_mail(
                    subject='❌ Votre rapport de dépense a été rejeté',
                    message=f"""
                    Bonjour {rapport.employee.username},
                    
                    Nous regrettons de vous informer que votre rapport de dépense concernant 
                    {rapport.materiau_article} pour un montant de {rapport.prix_unitaire * rapport.quantité} FCFA a été rejeté.
                    
                    Commentaire du gestionnaire : {commentaire}
                    
                    Veuillez prendre les mesures nécessaires.
                    
                    Cordialement,
                    L'équipe de gestion des dépenses
                    """,
                    from_email="sanbasystemegestion@gmail.com",
                    recipient_list=[rapport.employee.email, "nasserdevtest@gmail.com"],
                    fail_silently=True
                    
                )
            except Exception as e:
                logger.error(f"Erreur envoi mail rejet rapport {e}")
                
        
        elif action == "modifier":
            rapport.status = "modifier"
            rapport.note = f'\n[A MODIFIER {commentaire}]'
            try:
                # Envoi d'un email de notification à l'employé
                send_mail(
                    subject='📝 Modifications requises pour votre rapport de dépense',
                    message=f"""
                    Bonjour {rapport.employee.username},
                    
                    Votre rapport de dépense concernant {rapport.materiau_article} 
                    nécessite des modifications avant validation.
                    
                    Commentaire du gestionnaire : _ {commentaire} _
                    
                    Merci de bien vouloir apporter les modifications nécessaires.
                    
                    Cordialement,
                    L'équipe de gestion des dépenses
                    """,
                    from_email="sanbasystemegestion@gmail.com",
                    recipient_list=[rapport.employee.email, "nasserdevtest@gmail.com"],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur envoi mail modification rapport {e}")
        
        if commit:
            rapport.save()
        
        return rapport
    
    
    

                                  
    

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'telephone', 'email', "specialite"]
        
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        
        self.fields['nom'].required=True
        
         # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300 mb-4"
        
        for field_name, field in self.fields.items():
            # Classes de base
            field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-300 mb-4 center"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-300"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
       
       
        
class updateRapportFournisseurForm(forms.ModelForm):
    class Meta:
        model = RapportDepense
        fields = ["fournisseur"]
        
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        
         # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300 mb-4"
        
        for field_name, field in self.fields.items():
            # Classes de base
            field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-300 mb-4 center"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-300"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
            
        