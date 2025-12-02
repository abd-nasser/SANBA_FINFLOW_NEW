from django.shortcuts import render
from django.views.generic import TemplateView #pour les vues basées sur template
from django.contrib.auth.mixins import LoginRequiredMixin #Sécurité : Oblige la connexion
from django.db.models import Count, Sum, Avg, Q #Magie des requetes Django
from django.utils import timezone # Gestion du temps dans Django
from datetime import timedelta #calcul des dates

from client_app.models import Client #Modèles
from chantier_app.models import Chantier
from client_app.models import Contrat
from directeur_app.models import FondDisponible



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
        
        # 5. ALERTE & NOTIFICATIONS (ce qui nécessite attention)
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
        ca_par_mois = [] #Liste lide à remplire
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
            'top-clients_ca': top_clients_ca, # meilleurs clients
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
        
        return {
            "nombre_chantier_par_status": chantiers_par_status,
            "nombre_chantier_en_retard": chantiers_retard,
            "performance_type_travaux":performance_travaux
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
                'message':f'{contrats_non_signes} contrats(s) en attenete de signature',
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
        if fond_disponible.montant < 200000:
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
        return {
            "alerte":alerts,
            "chantiers_en_retard":chantiers_retard,
            "contrats_non_signes":contrats_non_signes,
            "client_sans_chantiers":client_sans_chantiers,
            "fond_disponible_bas":fond_disponible,
            "clients_anniversaire":clients_anniversaire,
            
        }
    
    def calculate_taux_encaisse(self):
        """Calcule le taux d'encaissement moyen"""
        contrats = Contrat.objects.all()
        if not contrats.exists():
            return 0
        total_montant = sum(c.montant_total for c in contrats)
        total_encaisse = sum(c.montant_encaisse for c in contrats)
        
        return (total_encaisse/total_montant*100) if total_montant>0 else 0