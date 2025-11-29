from django.db import models

from auth_app.models import Personnel



class Chantier(models.Model):
    
    """
    toutes les informations relatives aux chantiers
    """
    TYPE_TRAVAUX_CHOICES = [
        ("charpente_metallique", "Charpente Métallique"),
        ("toiture_tole", "Toiture en Tôle"),
        ("couverture", "Couverture"),
        ("isolation", "Isolation"),
        ("ventilation", "Ventilation"),
        ("etancheite", "Étanchéité"),
        ("garde_corps", "Garde-Corps"),
        ("escalier_metal", "Escalier en Métal"),
        ("porte_grillee", "Porte/Grille Métallique"),
        ("mixte", "Travaux Mixtes"),
        ("autre", "Autre")
    ]


    TYPE_BATIMENT_CHOICES = [
        ("maison_individuelle", "Maison Individuelle"),
        ("appartement", "Appartement"),
        ('entrepot', 'Entrepôt'),
        ('usine', 'Usine'),
        ('bureau', 'Bureau'),
        ('commerce', 'Commerce'),
        ('ferme', 'Batiment Agricole'),
        ('batiment_public', 'Batiment Public'),
        ('autre', 'Autre')
    
    ]

    STATUS_CHANTIER_CHOICES = [
        ("devis","Devis en Cours"),
        ('planification', 'Planification'),
        ('en_cours', 'En Cours'),
        ('suspendu', 'Suspendu'),
        ('termine', 'Terminé'),
        ('facturee', 'Facturée'),
        ('paye', 'Payée'),
        ('annule', 'Annulé')
    ]

    client = models.ForeignKey("client_app.Client", related_name="chantiers", on_delete=models.CASCADE)
    
    #reférence unique du chantier
    reference = models.CharField(max_length=100, unique=True)
    
    #nom_chantier = un nom facile à retenir pour le chantier
    nom_chantier = models.CharField(max_length=200)
    
    #LOCALISATION PRÉCISE
    adresse_chantier = models.TextField()
    adresse_chantier = models.CharField(max_length=100)
    quartier_chantier = models.CharField(max_length=100, null=True, blank=True)
    ville_chantier = models.CharField(max_length=100, null=True, blank=True)
    pays_chantier = models.CharField(max_length=100)
    
    #gps_latitude et longitude = position gps du chantier
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    #caractéristiques du chantier
    type_travaux = models.CharField(max_length=50, choices=TYPE_TRAVAUX_CHOICES)
    type_batiment = models.CharField(max_length=50, choices=TYPE_BATIMENT_CHOICES)
    surface_totale = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True) #en m2
    
    #hauteur_batiment = hauteur totale du batiment en metres
    hauteur_batiment = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    #desceription = description détaillée du chantier
    description_detaille = models.TextField(null=True, blank=True)
    
    #planning 
    #date_debut_prevue et date_fin_prevue = dates prévues pour le chantier
    date_debut_prevue = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)   
    
    #date_debut_reelle et date_fin_reelle = dates réelles du chantier
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    
    #duree_estimee = durée estimée du chantier en jours
    duree_estimee = models.IntegerField(null=True, blank=True)  
    
    #EQUIPE 
    chef_de_chantier = models.ForeignKey(Personnel, related_name="chantiers_chef", on_delete=models.SET_NULL, null=True, blank=True)
    
    #equipe_affectee = une liste des employés affectés au chantier
    equipe_affectee = models.ManyToManyField(Personnel, related_name="chantiers_participants", blank=True)
    
    
    #STATUT ET SUIVI FINANCIER
    #budget_total = budget total alloué au chantier
    budget_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    #cout_materiaux_estime = coût estimé des matériaux
    cout_materiaux_estime = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    #cout_main_oeuvre_estime = coût estimé de la main d'oeuvre
    cout_main_oeuvre_estime = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    #marge_beneficiaire_estimee = marge bénéficiaire estimée
    marge_beneficiaire_estimee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    #STATUS ET  SUIVI
    status_chantier = models.CharField(max_length=50, choices=STATUS_CHANTIER_CHOICES, default='devis')
    
    #priorité = priorité du chantier
    priorite = models.CharField(max_length=20, 
                               choices=[
                                           ('basse', 'Basse'),
                                           ('normale', 'Normale'),
                                           ('haute', 'Haute'),
                                           ('urgente', 'Urgente')
                                       ], 
                               default='normale')
    
    #DOCUMENTS
    # plans_et_specifications = fichiers liés aux plans du chantier
    plans_joins = models.BooleanField(default=False)
    photos_avant = models.BooleanField(default=False)
    photos_apres = models.BooleanField(default=False)
    
    #METADATA AUTOMATIQUE
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        """configuration spécial pour django"""
        verbose_name = "Chantier"
        verbose_name_plural = "Chantiers"
    
    def __str__(self):
        """affichage dans l'admin"""
        return f"{self.reference} - {self.nom_chantier} - {self.client}"
    
    
    def calculer_progression(self):
        """Calcule combien de pourcentage du chantier est terminé
        """
        return 0 # a ameliorer plus tard
    
    @property
    def est_en_retard(self):
        """Vérifie si le chantier est en retard par rapport à la date de fin prévue
        """
        if self.date_fin_prevue and self.date_fin_reelle:
            return self.date_fin_reelle > self.date_fin_prevue
        return False
