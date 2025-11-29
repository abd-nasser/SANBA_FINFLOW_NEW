from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin #Sécurité
from django.views.generic import ListView, CreateView , DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages


from .models import Chantier
from .models import Client  # Import the Client model
from .forms import ClientForm# Import the ClientForm



class ClientListView(LoginRequiredMixin, ListView):
    """Récupère tous les liste de la base ,
        Les envoie au templates,
        Affiche le template
    
    """
    model = Client #le model utilsé
    template_name = "client_templates/client.html"
    context_object_name = "clients" #comment on l'appel dans le templates
    paginate_by = 20 # 20 clients par page 
    
    def get_queryset(self):
        """Personnalise quel client on souhaite afficher
           par defaut = Client.objects.all()
        """
        
        return Client.objects.all().order_by("nom")
    
    

class ClientCreateView(LoginRequiredMixin, CreateView):
    
    """Affichage automatique d'un formulaire vide
       valide les données qand on fait un submit
       crée le client en bd
       redirect vers list client 
    """
    
    model = Client
    form_class = ClientForm 
    template_name = "modal/ajouter_client.html"
    success_url = reverse_lazy("client_app:liste-client")
    
    def form_valid(self, form):
        """
        Méthode appelée quand le formulaire est valide
        On peut faire des actions supplémentaires ici
        """
        #Ajoute le commercial connecté automatiquement
        if hasattr(self.request.user, 'personnel'):
            form.instance.commercial_attache = self.request.user.personnel
        #Message de succès
        messages.success(self.request, f"Client {form.instance.nom} à été ajouté avec succès")
        
        #Sauvegarde le client et redirige
        return super().form_valid(form)
        
    

class ClientDetailView(LoginRequiredMixin, DetailView):
    """
    Cette vue  affiche les details d'un seul client
    elle recoit l'ID du client dans l'url
    """
    
    model = Client
    template_name = "client_templates/detail_client.html"
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        """On peut ajouter des données supplémentaires au template"""
        
        #Récupère le contexte de base (le client)
        context = super().get_context_data(**kwargs)
        
        #Ajoute les chantiers de ce client
        context["client_all_chantiers"]=self.object.chantiers.all()
        return context
    

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier les informations d'un client existant
    """
    model = Client
    form_class = ClientForm
    template_name = "modal/modifier_client.html"
    success_url = reverse_lazy("client_app:liste-client")
    
    def form_valid(self, form):
        """Méthode appelée quand le formulaire est valide
        On peut faire des actions supplémentaires ici
        """
        #Message de succès
        messages.success(self.request, f"Client {form.instance.nom} à été modifié avec succès")
        
        #Sauvegarde le client et redirige
        return super().form_valid(form)
    

class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """Supprimer un client existant
    """
    model = Client
    template_name = "modal/supprimer_client.html"
    success_url = reverse_lazy("client_app:liste-client")
    
    def delete(self, request, *args, **kwargs):
        """Méthode appelée lors de la suppression
        On peut faire des actions supplémentaires ici
        """
        client = self.get_object()
        messages.success(self.request, f"Client {client.nom} à été supprimé avec succès")
        
        return super().delete(request, *args, **kwargs)