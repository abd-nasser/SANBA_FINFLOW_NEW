
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView #pour les vues basées sur template
from django.contrib.auth.mixins import LoginRequiredMixin #Sécurité : Oblige la connexion
from django.db.models import F, Count, Sum, Avg, Q, Value, Max, DecimalField#Magie des requetes Django
from decimal import Decimal
from django.utils import timezone # Gestion du temps dans Django
from django.db.models.functions import TruncMonth, Coalesce
from datetime import timedelta #calcul des dates
from pprint import pprint


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
        """ANALYTICS FINANCIERS AVANCES - VERSION AMÉLIORÉE"""
        
        # ===========================================
        # 1. CA PAR MOIS (6 DERNIERS MOIS CALENDAIRES)
        # ===========================================
        ca_par_mois = []
        
        # Obtenir la date du jour
        today = timezone.now()
        
        for i in range(5, -1, -1):  # 6 derniers mois
            # Calculer le mois cible
            # PROBLEME: timedelta(days=30*i) donne des approximations
            # Si aujourd'hui = 31 mars, -30 jours = 1 mars (OK)
            # Si aujourd'hui = 31 janvier, -30 jours = 1 janvier (Problème!)
            
            target_date = today - timedelta(days=30*i)
            
            # Alternative plus précise (si tu as dateutil)
            # target_date = today - relativedelta(months=i)
            
            # Filtrer les contrats du mois
            ca_mois = Contrat.objects.filter(
                date_signature__year=target_date.year,
                date_signature__month=target_date.month
            ).aggregate(
                total=Sum('montant_total')
            )["total"]
            
            # Si aucun contrat, ca_mois = None -> convertir en 0
            ca_mois_float = float(ca_mois if ca_mois is not None else 0)
            
            # Format du mois : "Janv 25", "Fév 25", etc.
            mois_formate = target_date.strftime("%b %y")
            
            # Stocker les données
            ca_par_mois.append({
                "mois": mois_formate,
                "ca": ca_mois_float
            })
            
            # DEBUG: Pour vérifier les dates
            print(f"Mois {i}: {mois_formate}, CA: {ca_mois_float}")
        
        # ===========================================
        # 2. TOP CLIENTS
        # ===========================================
        top_clients_ca = Client.objects.annotate(
            total_ca=Sum('chantiers__contrats__montant_total')
        ).exclude(
            total_ca=None  # ou total_ca__isnull=True
        ).order_by(
            '-total_ca'
        )[:5]  # Les 5 premiers seulement
        
        # ===========================================
        # 3. PRÉPARER LES DONNÉES POUR TEMPLATE
        # ===========================================
        return {
            'ca_par_mois': ca_par_mois,
            'top_clients_ca': top_clients_ca,
            'taux_encaisse_moyen': self.calculate_taux_encaisse(),
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
        """ANALYTICS CHANTIERS - Performance et efficacité des projets"""
        
        # ===========================================
        # 1. DISTRIBUTION PAR STATUT
        # ===========================================
        chantiers_par_status = Chantier.objects.values("status_chantier").annotate(
            total=Count('id')
        ).order_by('-total')
        
        # ===========================================
        # 2. CHANTIERS EN RETARD (en cours + date dépassée)
        # ===========================================
        chantiers_retard = Chantier.objects.filter(
            status_chantier='en_cours',
            date_fin_prevue__lt=timezone.now().date()
        ).count()
        
        # ===========================================
        # 3. PERFORMANCE PAR TYPE DE TRAVAUX
        # ===========================================
        performance_travaux = Chantier.objects.filter(
            type_travaux__isnull=False  # Exclure les chantiers sans type
        ).values('type_travaux').annotate(
            total=Count('id'),
            budget_moyen=Avg("budget_total"),
            duree_moyenne=Avg("duree_estimee"),
            # Ajout du budget total pour référence
            budget_total=Sum("budget_total")
        ).order_by('-total')
        
        # ===========================================
        # 4. DONNÉES POUR RADAR CHART
        # ===========================================
        radar_data = []
        
        for perf in performance_travaux:
            # Récupérer les valeurs avec gestion des None
            total = perf['total'] or 0
            budget_moyen = perf['budget_moyen'] or 0
            duree_moyenne = perf['duree_moyenne'] or 0
            
            # Calcul de l'efficacité (budget par jour)
            if duree_moyenne > 0:
                efficacite = float(budget_moyen) / float(duree_moyenne)
            else:
                efficacite = 0
            
            # Créer l'entrée pour le radar
            radar_data.append({
                'type_travaux': perf['type_travaux'],
                'label': perf['type_travaux'].replace("_", " ").title(),
                'nombre': total,
                'budget_moyen': float(budget_moyen),
                'duree_moyenne': float(duree_moyenne),
                'efficacite': float(efficacite),
                # Données originales pour référence
                'budget_total': float(perf['budget_total'] or 0)
            })
            
            if len(radar_data) < 3:
                radar_data.extend([
                    {
                        'type_travaux': 'charpente_metallique',
                'label': 'Charpente Metallique',
                'nombre': 8,
                'budget_moyen': 4500000,
                'duree_moyenne': 45,
                'efficacite': 100000,
                'nombre_norm': 75,
                'budget_norm': 90,
                'duree_norm': 60,
                'efficacite_norm': 85
            },
            {
                'type_travaux': 'menuiserie_metal',
                'label': 'Menuiserie Metal',
                'nombre': 5,
                'budget_moyen': 2800000,
                'duree_moyenne': 30,
                'efficacite': 93333,
                'nombre_norm': 50,
                'budget_norm': 70,
                'duree_norm': 40,
                'efficacite_norm': 70
            },
            {
                'type_travaux': 'serrurerie',
                'label': 'Serrurerie',
                'nombre': 12,
                'budget_moyen': 1200000,
                'duree_moyenne': 15,
                'efficacite': 80000,
                'nombre_norm': 100,
                'budget_norm': 40,
                'duree_norm': 20,
                'efficacite_norm': 60
            }
        ])    
        
        # ===========================================
        # 5. NORMALISATION POUR LE RADAR CHART (0-100)
        # ===========================================
        if radar_data:
            # Récupérer les valeurs maximales
            max_values = {
                'nombre': max((d['nombre'] for d in radar_data), default=1),
                'budget_moyen': max((d['budget_moyen'] for d in radar_data), default=1),
                'duree_moyenne': max((d['duree_moyenne'] for d in radar_data), default=1),
                'efficacite': max((d['efficacite'] for d in radar_data), default=1),
            }
            
            # Appliquer la normalisation (0-100)
            for data in radar_data:
                # Éviter la division par zéro
                data['nombre_norm'] = (data['nombre'] / max_values['nombre']) * 100 if max_values['nombre'] > 0 else 0
                data['budget_norm'] = (data['budget_moyen'] / max_values['budget_moyen']) * 100 if max_values['budget_moyen'] > 0 else 0
                data['duree_norm'] = (data['duree_moyenne'] / max_values['duree_moyenne']) * 100 if max_values['duree_moyenne'] > 0 else 0
                data['efficacite_norm'] = (data['efficacite'] / max_values['efficacite']) * 100 if max_values['efficacite'] > 0 else 0
                
                # Formater pour le template
                data['nombre_norm'] = round(data['nombre_norm'], 1)
                data['budget_norm'] = round(data['budget_norm'], 1)
                data['duree_norm'] = round(data['duree_norm'], 1)
                data['efficacite_norm'] = round(data['efficacite_norm'], 1)
        
        # ===========================================
        # 6. RETOUR DES DONNÉES
        # ===========================================
        return {
            "nombre_chantier_par_status": list(chantiers_par_status),
            "nombre_chantier_en_retard": chantiers_retard,
            "performance_type_travaux": list(performance_travaux),
            "radar_performance_data": radar_data,  # AVEC LES VALEURS NORMALISÉES
            # Statistiques supplémentaires
            "total_chantiers": Chantier.objects.count(),
            "chantiers_actifs": Chantier.objects.filter(status_chantier='en_cours').count(),
            "chantiers_termines": Chantier.objects.filter(status_chantier='termine').count(),
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
                Sum(F('rapports__prix_unitaire') * F('rapports__quantité'), 
                    filter=Q(rapports__status='valide')),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).filter(total_depenses__gte=0).order_by('-total_depenses')
              
        
        # Calculer le TOTAL GÉNÉRAL des dépenses validées
        total_general_depenses = Decimal('0')
        for item in depenses_par_categorie:
            total_general_depenses += item['total_depenses'] or Decimal('0')   
            
        print(f"=== DEBUG ===")
        print(f"Total général dépenses validées: {total_general_depenses}")
        
        print(f"Fond disponible: {fond_disponible.montant}")    
        
        
        # Ajout couleur et pourcentage
        for item in depenses_par_categorie:
            categorie = item['categorie'] 
            # Couleur
            type_dep = TypeDepense.objects.filter(
                categorie=categorie,
                est_actif=True
            ).first()
            item['couleur'] = type_dep.couleur if type_dep else '#CCCCCC'
            
            
            # Pourcentage en Decimal - CORRECTION ICI
            total_dep = item['total_depenses'] or Decimal('0')
            
            # Calculez le pourcentage par rapport au TOTAL DES DÉPENSES
            if total_general_depenses > Decimal('0'):
                # C'est ça la formule correcte pour un donut/chart
                item['total_pourcentage'] = (total_dep * Decimal('100')) / total_general_depenses
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
                    F('total_depenses_sum')*100/total_general_depenses
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