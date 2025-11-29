from django.db import models
from django.contrib.auth.models import AbstractUser


class Post(models.Model):
    nom = models.CharField(max_length=100)
    date_creation = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
class Personnel(AbstractUser):
    post = models.ForeignKey(Post,on_delete=models.CASCADE, null=True)
    telephone = models.CharField(max_length=100)
    date_de_naissance = models.DateField(null=True, blank=True)
    lieu_de_naissance = models.CharField(max_length=200)
    personne_a_prevenir_en_cas = models.TextField()
    
    def __str__(self):
        return self.username
    

