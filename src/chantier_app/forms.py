from django import forms
from .models import Chantier

class ChantierInfoForm(forms.ModelForm):
    """Les Infos obligatoires du chantier"""
    
    class Meta:
        model = Chantier
        fields = [
            'nom_chantier',
            'client',
            'reference',
            'type_travaux',
            'type_batiment',    
        ]
        
        labels = {
            'nom_chantier': 'Nom du Chantier',
            'client': 'Client',
            'reference': 'Référence unique du chantier',
            'type_travaux': 'Type de Travaux',
            'type_batiment': 'Type de Bâtiment',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre tous les champs obligatoires (sauf référence en modification)
        for field in self.fields:
            self.fields[field].required = True
        
        # 🎯 Verifie si c'est une modification
        if self.instance and self.instance.pk:
            # 🎯 MODIFICATION : référence en lecture seule
            self.fields['reference'].required = False  # Non requis
            self.fields['reference'].widget.attrs.update({
                'readonly': True,
                'disabled': True,  # Empêche l'envoi de la valeur
                'class': 'input input-bordered w-300 bg-base-200 opacity-75 cursor-not-allowed'
            })
            self.fields['reference'].help_text = "⚠️ Référence non modifiable"
        else:
            # 🎯 CRÉATION : champ normal
            self.fields['reference'].help_text = "Référence unique du chantier"
        
        # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300"
        
        for field_name, field in self.fields.items():
            # Skip reference si disabled
            if field_name == 'reference' and field.widget.attrs.get('disabled'):
                continue
            
            # Classes de base
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-300"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-full"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
    
    def clean_reference(self):
        """Validation intelligente qui gère création ET modification"""
        reference = self.cleaned_data.get('reference')
        
        # 🎯 Si modification, on garde TOUJOURS l'ancienne valeur
        if self.instance and self.instance.pk:
            # Si le champ est disabled, il ne sera pas dans cleaned_data
            # On retourne donc la valeur existante
            if 'reference' not in self.cleaned_data:
                return self.instance.reference
            
            # Si par hasard il y a une valeur (POST malgré disabled)
            # On l'ignore et on retourne l'ancienne
            return self.instance.reference
        
        # 🎯 Si création, on vérifie l'unicité
        if Chantier.objects.filter(reference=reference).exists():
            raise forms.ValidationError("Cette référence existe déjà")
        
        return reference
    
    def clean(self):
        """Nettoyage global du formulaire"""
        cleaned_data = super().clean()
        
        # 🎯 En modification, on s'assure que la référence reste inchangée
        if self.instance and self.instance.pk:
            cleaned_data['reference'] = self.instance.reference
        
        return cleaned_data 
    
    
    
    
    #################################
        

class ChantierLocalisationForm(forms.ModelForm):
    """Position Géographique du chantier"""
    class Meta:
        model = Chantier
        fields = ["adresse_chantier","pays_chantier",
                  "quartier_chantier", "ville_chantier",
                  "gps_latitude","gps_longitude"
                  
                  ]
        labels = {
            "adresse_chantier": "Adresse complète",
            "pays_chantier" : "Pays",
            "quartier_chantier": "Quartier",
            "ville_chantier": "Ville",
            "gps_latitude": "Latitude GPS",
            "gps_longitude": "Longitude GPS",
        }
        
        #widget = comment afficher le champ
        
        widget = {
            "adresse_chantier":forms.Textarea(attrs={'rows':3}),
        }
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            
            # Ici, certains champs son optionnels
        for field in ["gps_latitude", "gps_longitude"]:
            self.fields[field].required = False # pas obligatyoire
            
        for field in ["adresse_chantier","pays_chantier","ville_chantier","quartier_chantier"]:
            self.fields[field].required= True #Obligatoite   

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
            

class ChantierCaracteristiquesForm(forms.ModelForm):
    """Carateristique technique du chnatier"""
    class Meta:
        model = Chantier
        fields = [
                "surface_totale","hauteur_batiment",
                "description_detaille",
                "plans_joins","photos_avant",
                "photos_apres", "priorite"
                
                ]
        
        labels = {
            
            "surface_totale": "Surface totale (m²)",
            "hauteur_batiment": "Hauteur du bâtiment (m)",
            "description_detaille": "Description détaillée",
            "plans_joins": "Plans joints",
            "photos_avant": "Photos avant travaux",
            "photos_apres": "Photos après travaux",
            "priorite": "Priorité du chantier",
            
        }
    
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        #
        for field in self.fields:
            self.fields[field].required = False #auccun champs n'est obligatoire   
            
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
            
    
    
class ChantierPlanningForm(forms.ModelForm):
    """Les champs pour le plannig du Chantier"""
    
    class Meta:
        model = Chantier
        fields = [
            "date_debut_prevue","date_fin_prevue",
            "chef_de_chantier", "equipe_affectee",
            "duree_estimee"
        ]
        
        labels = {
            "date_debut_prevue": "Date de début prévue",
            "date_fin_prevue": "Date de fin prévue",
            "chef_de_chantier": "Chef de chantier",
            "equipe_affectee": "Équipe affectée",
            "duree_estimee" : "Durée estimé en jour"
        }
        
        widgets = {
            "date_debut_prevue":forms.DateInput(attrs={'type':'date'}),
            "date_fin_prevue": forms.DateInput(attrs={'type':'date'}),
            
        }
        
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
            
         # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300"
        
        for field_name, field in self.fields.items():
            # Classes de base
            field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-300"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-300"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
            
            

class ChantierBudgetForm(forms.ModelForm): 
    """Pour les infos budgetaire du chantier"""
    class Meta:
        model = Chantier
        fields = [
            "budget_total",
            "cout_materiaux_estime", "cout_main_oeuvre_estime",
            "marge_beneficiaire_estimee"
            
        ]
        
        labels = {
            "budget_total": "Budget total (Fcfa)",
            "cout_materiaux_estime": "Coût estimé des matériaux (Fcfa)",
            "cout_main_oeuvre_estime": "Coût estimé de la main d'œuvre (Fcfa)",
            "marge_beneficiaire_estimee": "Marge bénéficiaire estimée (Fcfa)",
        }
    
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields["budget_total"].required = True
            self.fields[field].required = False

         # Classes DaisyUI pour tous les champs
        base_classes = "input input-bordered w-300"
        
        for field_name, field in self.fields.items():
            # Classes de base
            field.widget.attrs['class'] = base_classes
            
            # Classes spécifiques par type
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = "select select-bordered w-300"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = "textarea textarea-bordered w-300"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = "checkbox"
            
    
    
    