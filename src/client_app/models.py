from django.db import models
from django.utils import timezone

from auth_app.models import Personnel
from chantier_app.models import Chantier



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
        ("autre", "Autre")
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
    date_premier_contact = models.DateField(null=True, blank=True)
    
    #commercial_attache = le commercial qui suit le client
    commercial_attache = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    
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
        """affichage dans l'admin"""
        if self.type_client == 'Entreprise':
            return f"{self.raison_sociale} - {self.telephone} -{self.ville} "
        else:
            return f"{self.nom} -{self.prenom} - {self.telephone} -{self.ville} "



    


class Contrat(models.Model):
    """tout les regle du jeu"""
    MODE_PAIEMENT_CHOICES = [
        ("comptant", "Comptant"),
        ('tranche', "Tranche"),
        ("credit", "Crédit"),
        ("autre", "Autre")
    ]
    
    #LIEN AVEC LE CHANTIER
    #chantier= à quel chantier ce contrat est lié
    chantier = models.OneToOneField(Chantier,related_name="chantiers", on_delete=models.CASCADE)
    
    #numéro unique pour contrat 
    referenre_contrat = models.CharField(max_length=50, unique=True)
    
    #quand le contrat été signé
    date_signature = models.DateField(null=True, blank=True)
    
    #comment le client souhaite payer
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default="comptant")
    
    #montant total du contrat
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    #combien de % le client paye au debut
    acompte_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    
    #en combien de fois il paye le reste 
    nombre_tranches = models.IntegerField(default=1)
    
    #SUIVIS DES PAIEMENTS
    #montant_encaisse = combien a été payé jusqu'à présent
    montant_encaisse = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    #datze_du_dernier_paiement = date du dernier paiement reçu
    date_du_dernier_paiement = models.DateField(null=True, blank=True)
    
    #DOCUMENTS IMPOERTANTS
    contrat_pdf = models.FileField(upload_to="contrats/", null=True, blank=True)
    
    #devis_initial = le premier qu'on a fait
    devis_initial = models.FileField(upload_to="devis/", null=True, blank=True)
    
    #CLAUSES SPECIALES
    # garanttie_mois = combien de mois on garantis notre travail
    garantie_mois = models.IntegerField(default=12)
    
    #notes_contractuelles = détails importants du contract
    notes_contractuelles = models.TextField(null=True, blank=True)
    
    class Meta:
        """configuration spécial pour django"""
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        
    def __str__(self):
        """affichage dans l'admin"""
        return f"Contrat {self.referenre_contrat} pour Chantier {self.chantier.nom_chantier}"
    
    @property
    def solde_restant(self):
        """Calcule combien il reste  à payer sur le contrat
        """
        return self.montant_total - self.montant_encaisse
    
    @property
    def pourcentage_encaisse(self):
        """Calcule le pourcentage du contrat qui a été payé
        """
        if self.montant_total > 0:
            return (self.montant_encaisse / self.montant_total) * 100
        return 0
    
    
    @property
    def montant_acompte(self):
        """Calcule le montant de l'acompte à payer
        """
        return (self.acompte_pourcentage / 100) * self.montant_total
    
    @property
    def est_signed(self):
        """Vérifie si le contrat a été signé
        """
        return self.date_signature is not None
    
    def enregistrer_paiement(self, montant_paye):
        """Enregistre un paiement fait par le client
        """
        self.montant_encaisse += montant_paye
        self.date_du_dernier_paiement = timezone.now().date()
        self.save()
        
        if self.montant_encaisse >= self.montant_total:
            # Contrat entièrement payé
            self.chantier.status_chantier = 'paye'
            self.chantier.save()
            
class TranchePaiement(models.Model):
    """pour les paiements en plusieurs tranches
    chaque tranche = une date ou le client doit payer
    
    """
    # contrat = à quel contrat cette tranche est liée
    contrat = models.ForeignKey(Contrat, related_name="tranches", on_delete=models.CASCADE)
    
    #numéro de la tranche
    numero_tranche = models.IntegerField()
    
    #montant = combien d'argent pour cette tranche
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    
    #date_prevue = quand le client doit payer cette tranche
    date_prevue = models.DateField()
    
    #date_reelle = quand le client a réellement payé cette tranche
    date_reelle = models.DateField(null=True, blank=True)
    
    #est_payee = si cette tranche a été payée
    est_payee = models.BooleanField(default=False)
    
    #motif = pourquoi cette tranche ...(ex: retard, problème technique, etc.)
    motif = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        verbose_name = "Tranche de Paiement"
        verbose_name_plural = "Tranches de Paiement"
        ordering = ['numero_tranche']
        
    def __str__(self):
        return f"Tranche {self.numero_tranche} du Contrat {self.contrat.referenre_contrat}"
    
    def marquer_comme_payee(self):
        """Marque cette tranche comme payée et enregistre la date réelle de paiement"""
        self.est_payee = True
        self.date_reelle = timezone.now().date()
        self.save()
        
        # met à jour le contrat parent 
        self.contrat.montant_encaisse += self.montant
        self.contrat.date_du_dernier_paiement = self.date_reelle
        self.contrat.save()
          