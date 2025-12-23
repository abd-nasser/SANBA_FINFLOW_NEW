
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView #pour les vues basées sur template
from django.contrib.auth.mixins import LoginRequiredMixin #Sécurité : Oblige la connexion
from django.db.models import F, Count, Sum, Avg, Q, Value, Max, DecimalField#Magie des requetes Django
from decimal import Decimal
from django.utils import timezone # Gestion du temps dans Django
from django.db.models.functions import TruncMonth, Coalesce
from datetime import timedelta #calcul des dates


from client_app.models import Client #Modèles
from chantier_app.models import Chantier
from contrat_app.models import Contrat
from directeur_app.models import FondDisponible
from employee_app.models import TypeDepense, RapportDepense, Fournisseur
from auth_app.models import Personnel

import logging
 
logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, TemplateView):
    """Cerveau du DASHBOARD
        templateView = vue qui affiche un template simple
        LoginRequiredMixin = Sécurité : pas d'accès sans authentification
    """
    
    template_name = 'dashboard_templates/dashboard.html'  #Template à afficher
 
    
    def get_context_data(self, **kwargs):
        """Methode Magique : Injecte des données dans le template
        Appelée automatiquement avant d'afficjer le template
        """
        # Récupère le contexte de base (toujous faire ça en premier)
        context = super().get_context_data(**kwargs)
        
        aujourdhui = timezone.now().date()
        mois_courant = aujourdhui.month
        annee_courante = aujourdhui.year 
        
        # 1.KPI - INDICATEURS CLES (chiffres importants)
        context.update(self.get_kpi_metrics())
        
        # 2. ANALYTICS FINANCIERS(argent, CA etc.)
        context.update(self.get_financial_analytics())
        
        # 3. ANALYTICS CLIENTS (qui sont nos clients)
        context.update(self.get_client_analytics())
        
        # 4. ANALYTICS CHANTIERS(Performance des projets)
        context.update(self.get_chantier_analytics())
        
        # 5 ANALYTICS_DEPENSE(suivis des sdepense)
        context.update(self.get_depense_analytics())
        
        # 6 ALERTE & NOTIFICATIONS (ce qui nécessite attention)
        context.update(self.get_alerts())
        
        
        
        return context #Retourne tout au template
    
    def get_kpi_metrics(self):
        """INDICATEURS CLES DE PERFORMANCE (KPI = Key Performance Indicators)
        Ce sont les chiffres les plus important pour le boss
        
        """
        return {
            #CLIENTS
            "total_client": Client.objects.count(), #Compte tous les cients
            "nouveaux_clients_mois":Client.objects.filter(date_premier_contact__month=timezone.now().month).count(), # filtre nombre Clients ce mois-ci
            'clients_fideles': Client.objects.filter(est_fidel=True).count(), #Filtre le nombre de client fidèles
            
            #CHANTIERS
            'total_chantiers': Chantier.objects.count(), #Compte tous les chantiers
            'chantiers_actifs':Chantier.objects.filter(status_chantier="en_cours").count(), #Filtre le nombre de chantier  par status = en cours
            'chantiers_termine_mois': Chantier.objects.filter(status_chantier="termine",date_fin_reelle__month=timezone.now().month).count(),#Filtre le nombre de chantier  par status terminée et ce mois 
            
            #FINANCES
            'chiffre_affaire_total': Contrat.objects.aggregate(total=Sum('montant_total'))['total'] or 0,
            'montant_encaisse_total':Contrat.objects.aggregate(total=Sum("montant_encaisse"))['total'] or 0,
            
        }
        
    def get_financial_analytics(self):
        """ANALYTICS FINANCIERS AVANCES
        Comprendre ou va l'argent et qui rapporte
        """
        
        #CA par mois  (6 derniers mois)
        ca_par_mois = [] #Liste vide à remplire
        for i in range(5, -1, -1): #range(5,-1, -1) = [5, 4, 3, 2, 1, 0]
            #calcul  de  la date : aujourd'hui -i mois 
            mois = timezone.now() - timedelta(days=30*i) # timedelta =  difference de temps
            
            #CA du mois spécifique
            ca_mois = Contrat.objects.filter(
                date_signature__year = mois.year, #contrats de l'année du mois 
                date_signature__month=mois.month  # contrats du mois
                
            ).aggregate(total=Sum('montant_total'))["total"] or 0 # somme des montants
            
        #Ajoute à la liste 
        ca_par_mois.append({
            "mois": mois.strftime("%b %y"), #Format "Nov 2025"
            "ca": float(ca_mois)
        })
        
        # Top 5 clients par chiffre d'affaires
        top_clients_ca = Client.objects.annotate( #annotae = ajoute une colone calculée
                                                 total_ca=Sum('chantiers__contrats__montant_total') # CA total par client
                                                 ).exclude(total_ca=None).order_by('-total_ca')[:5]
        
        return {
            'ca_par_mois': ca_par_mois, #Données pour le grahique
            'top_clients_ca': top_clients_ca, # meilleurs clients
            'taux_encaisse_moyen': self.calculate_taux_encaisse(), #Méthode séparée
            
        } 
        
    def get_client_analytics(self):
        """
        ANALYTICS CLIENTS
        pour comprendre notre clientèle
        """
        client_par_type = Client.objects.values("type_client").annotate(
            total=Count('id') #compte combien par type
        )
        
        source_clients = Client.objects.values('source_client').annotate(
            total=Count('id')
        )
        
        top_villes_clients = Client.objects.values('ville').annotate(
            total=Count('id')
        ).order_by("-total")[:5]
        
        return {
            "client_par_type":client_par_type,
            "source_clients":source_clients,
            "top_villes_clients":top_villes_clients,
        }
    
    def get_chantier_analytics(self):
        """ANALYTICS CHANTIERS
        Performance et efficacité des projets
        """
        chantiers_par_status = Chantier.objects.values("status_chantier").annotate(
            total=Count('id')
        )
        
        chantiers_retard = Chantier.objects.filter(
            Q(status_chantier='en_cours') & # status en cours et
            Q(date_fin_prevue__lt=timezone.now().date()) #Date dépassée
        ).count()
        
        performance_travaux = Chantier.objects.values('type_travaux').annotate(
            total = Count('id'), #nombre de chantiers par type_travaux
            budget_moyen=Avg("budget_total"),
            duree_moyenne=Avg("duree_estimee")
        )
        
        #Préparation des données pour Radar Chart
        radar_data = []
        for perf in performance_travaux:
            if perf['total'] > 0: #Evite les divisions par zéro
                efficacite = perf['budget_moyen'] or 0 / max(perf['duree_moyenne'] or 1)
            else:
                efficacite=0
                radar_data.append({
                    'type_travaux': perf['type_travaux'],
                    'label': perf['type_travaux'].replace("_"," ").title(),
                    'nombre': perf['total'],
                    'budget_moyen':perf['budget_moyen'] or 0,
                    'duree_moyenne':perf['duree_moyenne'] or 0,
                    'efficacite':efficacite
                })
        #Normalisation pour le radar(0-100)
        if radar_data:
            max_budget_moyen_par_type = max([d['budget_moyen'] for d in radar_data]) or 1
            max_duree_moyen_par_type= max([d['duree_moyenne']for d in radar_data]) or 1
            max_efficacite_par_type = max([d['efficacite']for d in radar_data]) or 1
            max_nombre_par_type = max([d['nombre']for d in radar_data]) or 1 
            
            for data in radar_data:
                data['budget_norm'] = (data['budget_moyen'] / max_budget_moyen_par_type) * 100
                data["duree_norm"] = (data['duree_moyenne'] / max_duree_moyen_par_type) * 100
                data["efficacite_norm"] = (data["efficacite"]/ max_efficacite_par_type) * 100
                data["nombre_norm"] = (data['nombre'] / max_nombre_par_type) * 100
                
        
        
        return {
            "nombre_chantier_par_status": chantiers_par_status,
            "nombre_chantier_en_retard": chantiers_retard,
            "performance_type_travaux":performance_travaux,
            "radar_performance_data":radar_data
        }

    def get_depense_analytics(self):
        """Analytics DES DEPENSES"""
       
        # 1-################__DEPENSE PAR CATEGORIE__##############
        fond_disponible = get_object_or_404(FondDisponible, id=1)
        
        # 1. DÉPENSES PAR CATÉGORIE (avec Decimal)
        depenses_par_categorie = TypeDepense.objects.filter(
            est_actif=True
        ).values('categorie').annotate(
            total_depenses=Coalesce(
                Sum(F('rapports__prix_unitaire') * F('rapports__quantité')),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).order_by('-total_depenses')
        
        # Ajout couleur et pourcentage
        for item in depenses_par_categorie:
            categorie = item['categorie']
            
            # Couleur
            type_dep = TypeDepense.objects.filter(
                categorie=categorie,
                est_actif=True
            ).first()
            item['couleur'] = type_dep.couleur if type_dep else '#CCCCCC'
            
            # Pourcentage en Decimal
            total_dep = item['total_depenses'] or Decimal('0')
            total_fond = fond_disponible.montant
            
            if total_fond > Decimal('0'):
                item['total_pourcentage'] = (total_dep * Decimal('100')) / total_fond
            else:
                item['total_pourcentage'] = Decimal('0')
            
            # 2-################__DEPENSE PAR TYPE DETAILLE__##############
            depense_par_type = TypeDepense.objects.filter(
                est_actif=True
            ).values("nom","categorie", "couleur").annotate(
                total_depenses_sum = Sum(F("rapports__prix_unitaire") * F("rapports__quantité")),
                nombre_utilisation = Count("rapports"),
                total_depenses=Sum(F("rapports__prix_unitaire") * F("rapports__quantité"))
            ).annotate(
                total_pourcentage =(
                    F('total_depenses')*100/fond_disponible.montant
                )
                ).order_by('-total_depenses_sum')
            
        # 3-################__TOTAL DEPENSES DU MOIS COURANT__##############
        mois_courant =timezone.now().month
        total_depenses_mois = RapportDepense.objects.filter(
            status='valide',
            date_depense__month=mois_courant
        ).aggregate(
            total = Coalesce(
                Sum(F("prix_unitaire") * F("quantité")),
                0,
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )['total'] or 0
        
        # 4-################__ DEPENSES PAR MOIS (6 derniers mois)__##############
        depense_par_mois = RapportDepense.objects.filter(
            status='valide',
            date_depense__gte=timezone.now() - timedelta(days=180)
        ).annotate(
            mois = TruncMonth('date_depense')
        ).values('mois').annotate(
            total = Coalesce(
                Sum(F("prix_unitaire") * F("quantité")),
                0,
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).order_by('mois')
        
        #convertir pour le template
        depense_par_mois_list = []
        for item in depense_par_mois:
            depense_par_mois_list.append({
                'mois':item['mois'],
                'total':float(item['total']) #convertit decimal en float pour chart.js
            })
        
        # 5-################__TOP EMPLOYES DEPENSIERS__##############
        top_employes_depense = Personnel.objects.values("username").annotate(
            employes_total_depense_sum=Sum(F("rapports_depense__prix_unitaire")*F('rapports_depense__quantité'))
        ).exclude(employes_total_depense_sum=None).order_by("-employes_total_depense_sum")
        
        # 6-################__TOP FOURNISSEUR__##############
        top_fournisseur = Fournisseur.objects.values('nom').annotate(
            total_achats_sum = Sum(F("achats__prix_unitaire")*F("achats__quantité"))
        ).exclude(total_achats_sum=None).order_by("-total_achats_sum")[:5] 
        
        
        # 7-################__RAPPORT AVEC LIEN DEMANDE DECAISSEMENT__############## 
        rapports_avec_lien = RapportDepense.objects.filter(
            demande_decaissement__isnull=False,
            status='valide'
        ).count()

        # 7-################__RAPPORT SANS LIEN DEMANDE DECAISSEMENT__############## 
        rapports_sans_lien = RapportDepense.objects.filter(
            demande_decaissement__isnull=True,
            status='valide'
        ).count()
        
        return {
            'depenses_par_categorie':list(depenses_par_categorie),
            'depense_par_mois':depense_par_mois_list,
            'total_depenses_mois':total_depenses_mois,
            'depense_par_type':depense_par_type,
            'top_employes_depense':top_employes_depense,
            'top_fournisseur':top_fournisseur,
            'couleurs_categories':self.get_couleurs_categories(),
            'rapports_avec_lien': rapports_avec_lien,
            'rapports_sans_lien': rapports_sans_lien,
            'taux_lien': (rapports_avec_lien / max(rapports_avec_lien + rapports_sans_lien, 1)) * 100
        }   
    
   




    
    
    def get_alerts(self):
        """ALERTES INTELLIGENTES
        Attire l'attention sur les problèmes importants
        """
        alerts = [] #list pour stocker les alertes
        
        #Chantier en retard
        chantiers_retard = Chantier.objects.filter(Q(status_chantier="en_cours") & #filtre chantier en cours
                                                   Q(date_fin_prevue__lt=timezone.now().date())
                                                   )
        if chantiers_retard.exists():
            alerts.append({
                'type':'warning',
                'message':f'🚨{chantiers_retard.count()} chantier(s) en retard',
                'lien': "/chantier/?status_chantier=en_cours",
            })
            
        #contrats non signés 
        contrats_non_signes = Contrat.objects.filter(
            date_signature__isnull=True #pas de date de signature
        ).count()
        if contrats_non_signes >0:
            alerts.append({
                "type":'info',
                'message':f'{contrats_non_signes} contrats(s) en attente de signature',
                'lien':'/contrats/' 
            })
        
        #client sans chantiers (opportunités manquées)
        client_sans_chantiers = Client.objects.filter(chantiers__isnull=True).count()
        if client_sans_chantiers > 0:
            alerts.append({
                'type':'info',
                "message":f"{client_sans_chantiers} client(s) sans chantier",
                'lien':'/clients'
            })
        
        #Fonds bas
        fond_disponible = FondDisponible.objects.get(id=1)
        if fond_disponible.montant < 100000:
            alerts.append({
                "type":'danger',
                "message":"Fonds très bas!",
            })
            
        #Client Anniversaires aujourd'hui
        clients_anniversaire = Client.objects.filter(
            date_de_naissance__month=timezone.now().month,
            date_de_naissance__day=timezone.now().day            
        )
        if clients_anniversaire.exists():
            for nom_aniv in clients_anniversaire:
                alerts.append({
                    "type":"info",
                    'message':f"Anniversaire client{nom_aniv.nom}"
                })
                
        # Rapports sans demande après 48h
        from datetime import timedelta
        rapports_tardifs = RapportDepense.objects.filter(
            demande_decaissement__isnull=True,
            date_creation__lte=timezone.now() - timedelta(hours=48),
            status__in=['soumis', 'brouillon']
        ).count()

        if rapports_tardifs > 0:
            alerts.append({
                'type': 'warning',
                'message': f'🚨 {rapports_tardifs} rapport(s) sans lien à une demande (>48h)',
                'lien': '/directeur/rapports-a-verifier/'
            })        
        
        return {
            "alerts":alerts,
            "chantiers_en_retard":chantiers_retard,
            "contrats_non_signes":contrats_non_signes,
            "client_sans_chantiers":client_sans_chantiers,
            "fond_disponible_bas":fond_disponible,
            "clients_anniversaire":clients_anniversaire,
            
        }


#Methode complement 
    def calculate_taux_encaisse(self):
        """Calcule le taux d'encaissement moyen"""
        contrats = Contrat.objects.all()
        if not contrats.exists():
            return 0
        total_montant = sum(c.montant_total for c in contrats)
        total_encaisse = sum(c.montant_encaisse for c in contrats)
        
        return (total_encaisse/total_montant*100) if total_montant>0 else 0 

    def get_couleurs_categories(self):
       #Récupère les couleurs depuis la base
       categories_couleurs = {}
       
       #Query optimisé: récupère totutes les catégories avec leur couleur
       types = TypeDepense.objects.filter(
           est_actif = True
       ).values('categorie', 'couleur').distinct()
       
       for type_item in types:
           categorie = type_item['categorie']
           couleur = type_item['couleur']
           
           #si la catégorie n'a pas encore de couleur ou si cette couleur est définie
           if categorie not in categories_couleurs or couleur:
               categories_couleurs[categorie]=couleur
               
       return couleur