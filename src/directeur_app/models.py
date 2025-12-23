from django.db import models
from auth_app.models import Personnel



class FondDisponible(models.Model):
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_ajout = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.montant}--{self.date_ajout}'


class Historique_dajout_fond(models.Model):
    nom = models.ForeignKey(Personnel, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.nom}--{self.montant}--{self.date_ajout}'