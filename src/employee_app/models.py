from django.db import models
from auth_app.models import Personnel
from chantier_app.models import Chantier
from django.core.validators import MinValueValidator, MaxValueValidator



class TypeDepense(models.Model):
    CATEGORIE_CHOICES = [
        ("materiaux", 'Matériaux'),
        ("transport", "Transport"),
        ("main_oeuvre", "main d'oeuvre"),
        ("frais_divers","Frais divers"),
        ("administration",'Administration'),
        ("autre", "Autre")
    ]
    
    COULEUR_CHOICES = [
        ('#FF6384', 'Rouge'),      # Matériaux
        ('#36A2EB', 'Bleu'),       # Transport 
        ('#9966FF', 'Violet'),     # Main d'oeuvre 
        ('#FFCE56', 'Jaune'),      # Frais divers
        ('#4BC0C0', 'Turquoise'),  # Administration 
        ('#FF9F40', 'Orange'),     # Autre
    ]
    
    nom = models.CharField(
        max_length=200,
        unique=True,
        help_text="Ex: Reparation appareil, Achat tole, Location camion, Salaire ouvrier"
    )
    categorie = models.CharField(max_length=50,
                                 choices=CATEGORIE_CHOICES,
                                 default='materiaux',
                                 help_text="choix du type de depense"
                                 )
    
    couleur = models.CharField(
        max_length=50,
        choices=COULEUR_CHOICES,
        default='#FF6384',
        help_text='Choix de la couleur pour type de depense'
     
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description détaillé du ty de depense"
    )
    
    est_actif = models.BooleanField(
        default=True,
        help_text="Désactiver pour masquer ce type sans supprimer l'historique"
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        help_text="Ordre d'affichage dans les liste déroulantes"
    )
    
    date_de_creation = models.DateTimeField(auto_now_add=True)
    date_de_modification = models.DateField(auto_now=True)
    
    class Meta:
        ordering = ['ordre_affichage', 'nom'] #tri intelligent
        verbose_name = 'Type de depense'
        verbose_name_plural = "Type de dépense"
    
    def __str__(self):
        return f"{self.get_categorie_display()}"
    
    @property
    def total_depenses(self):
        """TOTAL des dépenses de ce type"""
        from django.db.models import Sum
        total = self.rapports.aggregate(
            total=Sum(models.F('prix_unitaire')*models.F('quantité'))
        )['total'] or 0
        
    @property
    def nombre_utilisations(self):
        """Combien de fois ce type de depense à été fait"""
        return self.rapports.count()
    
    @property
    def moyenne_depense(self):
        """Depense moyenne pour ce type"""
        if self.nombre_utilisations > 0:
            return self.total_depenses/self.nombre_utilisations
        return 0
    
    def get_statistique_mois(self, mois=None, annee=None):
        """Statistique pour un mois spécifique"""
        from django.db.models import Sum, Count, Avg
        list_type_depense_valide = self.rapports.filter(status="valide")
        
        if mois and annee:
            list_type_depense_valide_ce_mois = list_type_depense_valide.filter(
                date_depense__month=mois,
                date_depense__year=annee
            )
        stats = list_type_depense_valide_ce_mois.aggregate(
            total = Sum(models.F('prix_unitaire')*models.F('quantité')),
            nombre = Count('id'),
            moyenne = Avg(models.F('prix_unitaire')*models.F('quantité'))
        )
        
        return{
            'total':stats['total'] or 0,
            'nombre':stats['nombre'] or 0,
            'moyenne': stats['moyenne'] or 0,
        }
    
        
    
class Fournisseur(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(null=True, blank=True)
    specialite = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name_plural = "Fournisseurs"
        ordering = ["nom"]
        
    
    def __str__(self):
        return self.nom
    
    @property
    def total_achats(self):
        """Total des achats chez ce fournisseur"""
        from django.db.models import Sum
        total = self.achats.aggregate(
            total=Sum(models.F("prix_unitaire")*models.F("quantité"))
        )["total"] or 0
        return total


class RapportDepense(models.Model):
    employee = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name="rapports_depense")
    
    demande_decaissement = models.ForeignKey(
        'secretaire_app.DemandeDecaissement',  # Assure-toi que c'est le bon chemin
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_depense',
        verbose_name="Demande de décaissement liée",
        help_text="Lien avec la demande d'argent préalable"
    )
    
    type_depense = models.ForeignKey(TypeDepense, on_delete=models.CASCADE, related_name='rapports')
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, related_name="depenses", null=True, blank=True)
    materiau_article = models.CharField(max_length=200, null=True, blank=True)
    
    prix_unitaire = models.DecimalField(max_digits=10, 
                                        decimal_places=2, 
                                        validators=[MinValueValidator(0)] #prix pas negatif
                                        )
    
    quantité = models.IntegerField(default=1,
                                   validators=[MinValueValidator(1)] #quantité minimum 1
                                   )
    fournisseur_not_db = models.CharField(max_length=75, null=True, blank=True)
    
    fournisseur = models.ForeignKey(Fournisseur, 
                                    on_delete=models.SET_NULL, 
                                    null=True, blank=True, 
                                    related_name="achats"
                                    )
    
    facture = models.ImageField(upload_to="images/photo_facture/%Y/%m/%d", 
                                null=True, 
                                blank=True)
    
    date_depense = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("brouillon", 'Brouillon'),
            ("soumis", 'Soumis'),
            ('valide','validé'),
            ('rejete', "Rejeté")
                 ],
        default='brouillon'
    )
    
    note = models.TextField(blank=True)
    
    class Meta:
        ordering=['-date_creation']
        verbose_name = "Rapport de depense"
        verbose_name_plural = "Rapports de depense"
        
        
    def total(self):
        """CALCUL DU TOTAL AVEC ARRONDI"""
        return round(self.prix_unitaire*self.quantité, 2)
    
    @property #pour usage template
    def total_affichage(self):
        return f'{self.total():,} FCFA' #Format avec virgules
    
    def __str__(self):
        return f'{self.employee.username}-{self.type_depense.nom} total={self.total_affichage}'
    
