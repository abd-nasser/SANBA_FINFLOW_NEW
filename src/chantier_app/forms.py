from django import forms
from .models import Chantier

class ChantierInfoForm(forms.ModelForm):
    """Les Infos obligatoires du chantier
    """
    class Meta :
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
    ###method pour reference du chantier
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 🎯 MAGIE : self.instance nous dit si on est en création ou modification
        if self.instance == self.instance.pk:
            # 🎯 MODIFICATION : référence en lecture seule
            self.fields['reference'].widget.attrs.update({
                'readonly': True,
                'class': 'form-control-plaintext bg-light'
            })
            self.fields['reference'].help_text = "Réference non modifiable"
        else:
            # 🎯 CRÉATION : champ normal
            self.fields['reference'].help_text = "Référence unique du chantier"
    
    def clean_reference(self):
        """Validation intelligente qui gère création ET modification"""
        reference = self.cleaned_data.get('reference')
        
        # 🎯 Si modification, on garde l'ancienne valeur
        if self.instance == self.instance.pk:
            return self.instance.reference  # ← Ignore la nouvelle valeur
        else:
            # 🎯 Si création, on vérifie l'unicité
            if Chantier.objects.filter(reference=reference).exists():
                raise forms.ValidationError("Cette référence existe déjà")
            
        return reference   
    
    
    
    
    #################################
        
    def __init__(self, *args, **kwargs):
        """Méthode spéciale qui s'exécute à la création du formulaire"""
        #Appelle la versiobn parent
        super().__init__(*args, **kwargs)

        #rend tous les champs obligatoires
        for field in self.fields:
            self.fields[field].required = True #Tous les champs requis 
                

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
        for field in ["ville_chantier","quartier_chantier","gps_latitude", "gps_longitude"]:
            self.fields[field].required = False # pas obligatyoire


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
    
    
class ChantierPlanningForm(forms.ModelForm):
    """Les champs pour le plannig du Chantier"""
    
    class Meta:
        model = Chantier
        fields = [
            "date_debut_prevue","date_fin_prevue",
            "date_debut_reelle","date_fin_reelle",
            "chef_de_chantier", "equipe_affectee",
        ]
        
        labels = {
            "date_debut_prevue": "Date de début prévue",
            "date_fin_prevue": "Date de fin prévue",
            "date_debut_reelle": "Date de début réelle",
            "date_fin_reelle": "Date de fin réelle",
            "chef_de_chantier": "Chef de chantier",
            "equipe_affectee": "Équipe affectée",
        }
        
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
            

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
    
    
    
    