from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin #Sécurité
from django.views.generic import ListView, CreateView , DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q

from chantier_app.models import Chantier
from .models import Client  # Import the Client model
from .forms import ClientForm # Import the ClientForm
from contrat_app.models import Contrat
from secretaire_app.forms import DemandeDecaissementForm
from secretaire_app.models import DemandeDecaissement
from directeur_app.models import FondDisponible
from auth_app.form import ChangeCredentialsForm



class ClientListView(LoginRequiredMixin, ListView):
    """Récupère tous les liste de la base ,
        Les envoie au templates,
        Affiche le template
    
    """
    model = Client #le model utilsé
    template_name = "client_templates/client.html"
    context_object_name = "clients" #comment on l'appel dans le templates
    paginate_by = 20 # 20 clients par page 
    
    def get_template_names(self):
        """retourne le template partials si requete HTMX"""
        if self.request.headers.get('HX-request'):
            #si requet HTMX -> retourne slmt le tableau(pas toute la page)
            return ["partials/liste_client_partial.html"]
        
        #requet normale -> retourne la page complète
        return[self.template_name]
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context["form"]= ClientForm()
        return context
    
    def get_queryset(self):
      """FILTRAGE INTELLIGENT AVEC OPTIMISATION DB"""
      #OPTIMISATION CRITIQUE: select_related
      queryset = Client.objects.all().select_related(
          'commercial_attache'
      )
       ########################__ 1️⃣ FILTRE PAR TYPE_CLIENT __############################
      type_client = self.request.GET.get('type_client')
      if type_client:
          queryset = queryset.filter(type_client=type_client)
          
          
    #########################__ # 2️⃣ FILTRE VILLE __############################
      ville = self.request.GET.get("villes")
      if ville:
          queryset = queryset.filter(ville=ville)
          
     ########################__ # 3️⃣ FILTRER PAR POTENTIEL CLIENT __############################     
      potentiel = self.request.GET.get("potentiel")
      if potentiel:
          queryset = queryset.filter(potentiel_client=potentiel)
          
     ########################__ # 3️⃣ FILTRER PAR CLIENT FIDEL __############################
      fidelite = self.request.GET.get("fidelite")
      if fidelite:
         queryset = queryset.filter(est_fidel=fidelite)
         
    ########################__ # 3️⃣ RECHERCHE TEXTE (nom chantier Ou client) __############################
      search_query = self.request.GET.get('q')
      if search_query:
          queryset = queryset.filter(
              
              Q(chantiers__nom_chantier__icontains=search_query)|
              Q(chantiers__reference__icontains=search_query)|
              Q(ville__icontains=search_query)|
              Q(quartier__icontains=search_query)|
              Q(pays__icontains=search_query)|
              Q(nom__icontains=search_query)|
              Q(prenom__icontains=search_query)|
              Q(total_contrats__icontains=search_query)
          
              
          )
             
      return queryset
    ########################__ # 3️⃣ RECHERCHE TEXTE (nom chantier Ou client) __############################
     
    
class ClientCreateView(LoginRequiredMixin, CreateView):
    
    """Affichage automatique d'un formulaire vide
       valide les données qand on fait un submit
       crée le client en bd
       redirect vers list client 
    """
    
    model = Client
    form_class = ClientForm 
    template_name = "client_templates/client.html"
    success_url = reverse_lazy("client_app:liste-client")
    
    
    def form_valid(self, form):
        """
        Méthode appelée quand le formulaire est valide
        On peut faire des actions supplémentaires ici
        """
        #Ajoute le commercial connecté automatiquement
        if hasattr(self.request.user, 'personnel'):
            form.instance.commercial_attache = self.request.user
        #Message de succès
        messages.success(self.request, f"Client {form.instance.nom} à été ajouté avec succès")
        
        #Sauvegarde le client et redirige
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return super().form_invalid(form)
    
    def get_template_names(self) -> list[str]:
        if self.form_invalid:
            if self.request.user.is_superuser or self.request.user.post.nom == "Directeur":
                return ["client_templates/client.html"]
         
            elif self.request.user.post.nom == "Sécretaire":
                return ["secretaire_templates/secretaire.html"]
            
            elif self.request.user.post.nom == "Comptable":
                return ["comptable_templates/comptable.html"]
      
            elif self.request.user.post.nom == "Employé":
                return ["employee_templates/creer_rapport.html"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"]= Client.objects.all().select_related(
          'commercial_attache'
      )
        context["dmd_form"] = DemandeDecaissementForm()
        context["list_demande"]= DemandeDecaissement.objects.all().order_by("-date_demande")[:3]
        context["fond"]=get_object_or_404(FondDisponible, id=1).montant
        context["ch_form"]=ChangeCredentialsForm(self.request.user)
        if self.form_invalid:
            context["open_client_modal"] = True
        return context
       
        
    
      
      
    
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
        client = self.object

        # AJOUTEZ cette ligne :
        context['form'] = ClientForm(instance=self.object)
        
        # Récupérer tous les contrats des chantiers de ce client
        context["client_all_contrats"] = Contrat.objects.filter(
            chantier__client=client
        )
        context["client_all_chantiers"] = client.chantiers.all()
        return context
       
    

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier les informations d'un client existant
    """
    model = Client
    form_class = ClientForm
    template_name = "client_templates/detail_client.html"
    def get_success_url(self):
        return reverse_lazy("client_app:detail-client", args=[self.object.pk])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # NE PAS recréer le form, il est déjà dans context['form']
        # Juste ajouter 'client' si nécessaire
        context['client'] = self.object
        if self.form_invalid:
            context["open_upd_client_modal"]=True
        return context
    
    
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