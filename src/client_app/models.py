from django.db import models
from django.utils import timezone

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



    


