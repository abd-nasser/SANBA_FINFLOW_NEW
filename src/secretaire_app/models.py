from django.db import models
from auth_app.models import Personnel
from chantier_app.models import Chantier

class DemandeDecaissement(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuvee_directeur', 'Approuvée par Directeur'),
        ('refusee_directeur', 'Refusée par Directeur'),
        ('approuvee_comptable', 'Approuvée par Comptable'), 
        ('refusee_comptable', 'Refusée par Comptable'),
    ]
    
    demandeur = models.ForeignKey(Personnel, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, null=True, blank=True)
    motif = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='en_attente')
    approuve_par = models.ForeignKey(
        Personnel, 
        related_name='demandes_approuvees', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    decaisse = models.BooleanField(default=False)
    date_demande = models.DateTimeField(auto_now=True)
    date_approbation = models.DateTimeField(null=True, blank=True)
    date_decaissement = models.DateTimeField(null=True, blank=True)
    reference_demande = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f'{self.reference_demande}'
    
    
