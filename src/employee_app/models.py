from django.db import models
from auth_app.models import Personnel
from chantier_app.models import Chantier



class TypeDepense(models.Model):
    nom = models.CharField(max_length=200)
    
    def __str__(self):
        return self.nom

class Fournisseur(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nom


class RapportDepense(models.Model):
    employee = models.ForeignKey(Personnel, on_delete=models.CASCADE)
    type_depense = models.ForeignKey(TypeDepense, on_delete=models.CASCADE)
    materiau_article = models.CharField(max_length=200, null=True, blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE)
    quantité = models.IntegerField(default=0)
    fournisseur = models.CharField(max_length=100, null=True, blank=True)
    facture = models.ImageField(upload_to="images/photo_facture/", null=True, blank=True)
    date = models.DateTimeField(auto_now=True)
    
    def total(self):
        return self.prix_unitaire*self.quantité
    
    def __str__(self):
        return f'{self.employee.username}-{self.type_depense.nom} total={self.total()}'
    
