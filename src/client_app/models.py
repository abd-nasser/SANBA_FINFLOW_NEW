from django.db import models
from django.utils import timezone
from contrat_app.models import Contrat
from auth_app.models import Personnel

class Client(models.Model):
    """
    toutes les informations relatives aux clients
    """
    #choix possible pour le type de client
    TYPE_CLIENT_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('institution', 'Institution publique'),
        ("promoteur", "Promoteur immobilier"), #ceux qui font dans le batiment
        ('autre', 'Autre')
    ]
    
    #type de batiment à travailler
    SECTEUR_ACTIVITE_CHOICES = [
        ('residential', 'Résidentiel'), #Maisons, appartements
        ('commercial', 'Commercial'), #Bureaux, magasins
        ('industriel', 'Industriel'), #Usines, entrepôts
        ('agricole', 'Agricole'), #Ferme, installations agricoles
        ('public', 'Public'),   #Écoles, hôpitaux, bâtiments gouvernementaux 
    ]
    
    #comment le client a connu l'entreprise
    SOURCE_CLIENT_CHOICES = [
        ('recommendation', 'Recommandation'),
        ('site_web', 'Site Web'),
        ('reseaux_sociaux', 'Réseaux Sociaux'),
        ('publicite', 'Publicité'),
        ('ancien_client', 'Ancien Client'),
        ('autre', 'Autre'),
        ('salon', 'Salon Professionnel'),

    ]
    
    #info principales du client
    type_client = models.CharField(max_length=50, choices=TYPE_CLIENT_CHOICES)
    
    #raison sociale = nom de l'entreprise
    raison_sociale = models.CharField(max_length=200, null=True, blank=True)
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    telephone = models.CharField(max_length=20)
    telephone_secondaire = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, null=True, blank=True)
    pays = models.CharField(max_length=100)
    date_de_naissance = models.DateField(null=True, blank=True)
    
    
    
    #INFOS BUSINESS 
    #sectreur d'activité du client
    secteur_activite = models.CharField(max_length=50, choices=SECTEUR_ACTIVITE_CHOICES, null=True, blank=True)
    source_client = models.CharField(max_length=50, choices=SOURCE_CLIENT_CHOICES, null=True, blank=True)
    
    #note_internes remarque sur le client
    notes_internes = models.TextField(null=True, blank=True)
    potentiel_client = models.CharField(max_length=20, 
                                        choices=[
                                                    ('faible', 'Faible'), #petit budget
                                                    ('moyen', 'Moyen'), #budget moyen
                                                    ('élevé', 'Élevé') #gros budget
                                                ], 
                                        null=True, blank=True, 
                                        default='moyen')
    
    #Suivi de la RElation 
    #date_premier_contact
    date_premier_contact = models.DateField(auto_now_add=True)
    
    #commercial_attache = le commercial qui suit le client
    commercial_attache = models.ForeignKey(Personnel, on_delete=models.SET_NULL,related_name="clients_attaches", null=True, blank=True)
    
    #est fidel = un client qui revient souvent
    est_fidel = models.BooleanField(default=False)
    
    #STATS AUTOMATIQUES
    #total_contrats = nombre total de contrats signés avec ce client
    total_contrats = models.IntegerField(default=0)
    
    #chiffre_affaires = montant total facturé à ce client
    chiffre_affaires_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    class Meta:
        """configuration spécial pour django"""
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        if self.type_client == 'entreprise':
            return self.raison_sociale
        return f"{self.nom} {self.prenom}"
    @property
    def contrats_signes(self):
        """Retourne tous les contrats signés avec ce client"""
        # Vérifie que le client existe dans la base
        if not self.pk:  # Si l'objet n'est pas encore sauvegardé
            return Contrat.objects.none()  # Retourne un queryset vide
        
        try:
            # Traverse: Client → Chantiers → Contrats
            # Utilise select_related pour optimiser
            return Contrat.objects.filter(chantier__client=self).select_related('chantier')
        except Exception as e:
            # En cas d'erreur (table inexistante, etc.)
            print(f"Erreur dans contrats_signes: {e}")
            return Contrat.objects.none()  # Retourne vide

    @property
    def total_contrats(self):
        """Nombre total de contrats signés"""
        try:
            count = self.contrats_signes.count()
            return count if count is not None else 0
        except Exception:
            return 0  # Retourne 0 en cas d'erreur

    @property
    def chiffre_daff_total(self):
        """CA total généré par ce client"""
        from django.db.models import Sum
        
        if self.total_contrats == 0:
            return 0  # Si pas de contrats, CA = 0
        
        try:
            # Aggregate peut retourner None si pas de données
            result = self.contrats_signes.aggregate(
                total=Sum('montant_total')
            )
            
            # Vérifie que 'total' existe et n'est pas None
            total = result.get('total')
            
            # Retourne 0 si total est None ou 0
            return float(total) if total is not None else 0.0
            
        except Exception as e:
            # Log l'erreur en développement
            import sys
            print(f"Erreur dans chiffre_daffaire_total: {e}", file=sys.stderr)
            return 0.0

    @property
    def chantiers_actifs(self):
        """Nombre de chantiers actifs"""
        # Vérifie que le client existe
        if not self.pk:
            return 0
        
        try:
            # Vérifie si le modèle Chantier existe et a le champ status
            count = self.chantiers.filter(status='en_cours').count()
            return count if count is not None else 0
        except Exception as e:
            # Gère le cas où 'chantiers' n'existe pas
            # ou où 'status' n'est pas un champ valide
            print(f"Erreur dans chantiers_actifs: {e}")
            return 0

    @property
    def a_des_contrats(self):
        """Vérifie si le client a au moins un contrat"""
        return self.total_contrats > 0

    @property
    def a_des_chantiers(self):
        """Vérifie si le client a au moins un chantier"""
        if not self.pk:
            return False
        try:
            return self.chantiers.exists()
        except Exception:
            return False

    @property
    def contrat_moyen(self):
        """Montant moyen par contrat"""
        if self.total_contrats > 0:
            try:
                return self.chiffre_daffaire_total / self.total_contrats
            except (ZeroDivisionError, TypeError):
                return 0
        return 0

    @property
    def dernier_contrat(self):
        """Date du dernier contrat signé"""
        if self.total_contrats > 0:
            try:
                dernier = self.contrats_signes.order_by('-date_signature').first()
                return dernier.date_signature if dernier else None
            except Exception:
                return None
        return None

    @property
    def statut_client(self):
        """Détermine le statut du client"""
        if not self.pk:
            return "Nouveau"
        
        if self.total_contrats == 0:
            return "Prospect"
        elif self.total_contrats == 1:
            return "Premier contrat"
        elif self.chiffre_daffaire_total > 1000000:  # Plus d'1 million
            return "Client premium"
        elif self.chantiers_actifs > 0:
            return "Client actif"
        else:
            return "Client historique"


    @property
    def nom_complet(self):
        """Retourne le nom complet du client"""
        return f"{self.nom} {self.prenom}"
    


