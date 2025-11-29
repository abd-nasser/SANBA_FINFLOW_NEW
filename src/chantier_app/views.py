from django.shortcuts import render, redirect
from formtools.wizard.views import SessionWizardView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView , DetailView, UpdateView, DeleteView
from django.contrib import messages
from chantier_app import models

from chantier_app.models import Chantier
from .forms import ChantierInfoForm, ChantierLocalisationForm, ChantierCaracteristiquesForm, ChantierPlanningForm, ChantierBudgetForm



#Chantiers Views
    
class ChantierListeView(LoginRequiredMixin, ListView):
    """Récupère tous les liste de la base ,
        Les envoie au templates,
        Affiche le template
    
    """
    model = Chantier #le model utilsé
    template_name = "chantiers_templates/chantiers_liste.html"
    context_object_name = "chantiers" #comment on l'appel dans le templates
    paginate_by = 20 # 20 clients par page 
    
    def get_queryset(self):
        """Personnalise quel client on souhaite afficher
           par defaut = Client.objects.all()
        """
        
        return Chantier.objects.all().order_by("-date_creation")
    

class ChantierCreateView(LoginRequiredMixin, SessionWizardView):
    
    form_list = [
        ("info", ChantierInfoForm),  #Etape 1: Infos de base
        ("localisation",ChantierLocalisationForm), ##Etape 2: Localisation
        ("caracteristiques",ChantierCaracteristiquesForm), #Etape 3: Caractéristiques
        ("planning",ChantierPlanningForm), #Etape 4: Planning
        ("budget",ChantierBudgetForm), #Etape 5: Budget
    ]
    template_name = "modal/ajouter_chantier.html"
    success_url = reverse_lazy("chantier_app:liste-chantier")
    
    
    def done(self, form_list, **kwargs):
        """
        Version corrigée pour gérer ManyToMany
        """
        chantier = Chantier()
        
        # 🎯 Étape 1 : Récupère tous les champs SAUF ManyToMany
        champs_simples = {}
        equipe_data = None
        
        
        #DEBUG pour equipe affectee
        for form in form_list:
            print(f" 🔍 Form {form.__class__.__name__} à equipe_affectee: {'equipe_affectee'in form.cleaned_data}")
            
            if 'equipe_affectee' in form.cleaned_data:
                equipe_data = form.cleaned_data["equipe_affectee"]
                print(f" 🎯 Equipe trouvée : {equipe_data}")
                print(f" 🎯 Type: {type(equipe_data)}")
                if equipe_data:
                    print(f"🎯 nombre de membres : {len(equipe_data)}")
                    for membre in equipe_data:
                        print(f"👤{membre.username}")
        
        for form in form_list:
            for field, value in form.cleaned_data.items():
                if value:
                    if field == 'equipe_affectee':
                        equipe_data = value  # 🎯 Garde l'équipe pour plus tard
                    else:
                        champs_simples[field] = value
        
        # 🎯 Étape 2 : Remplit le chantier avec les champs simples
        for field, value in champs_simples.items():
            setattr(chantier, field, value)
        
        # 🎯 Étape 3 : SAUVEGARDE le chantier (OBLIGATOIRE)
        chantier.save()
        
        # 🎯 Étape 4 : Maintenant on peut gérer l'équipe (ManyToMany)
        if equipe_data:
            chantier.equipe_affectee.set(equipe_data)  # ← ✅ CORRECT !
            print(chantier.equipe_affectee.all())
        # 🎯 Message de succès
        messages.success(self.request, f"Chantier {chantier.nom_chantier} créé avec succès !")
        
        return redirect('chantier_app:liste-chantier')
    

class ChantierDetailView(LoginRequiredMixin, DetailView):
    """Cette vue  affiche les details d'un seul chantier
    elle recoit l'ID du chantier dans l'url
    
    """
    
    model = Chantier
    template_name = "chantiers_templates/details_chantier.html"
    context_object_name = 'chantier'
    
    def get_context_data(self, **kwargs):
        """On peut ajouter des données supplémentaires au template"""
        #Récupère le contexte de base (le chantier)
        return super().get_context_data(**kwargs)
        

class ChantierUpdateView(LoginRequiredMixin, SessionWizardView):
    """
    🎯 MODIFICATION avec Wizard - Version SIMPLE
    Même structure que ta CreateView
    """
    
    form_list = [
        ("info", ChantierInfoForm),
        ("localisation", ChantierLocalisationForm), 
        ("caracteristiques", ChantierCaracteristiquesForm),
        ("planning", ChantierPlanningForm),
        ("budget", ChantierBudgetForm),
    ]
    template_name = "modal/modifier_chantier.html"
    
    def get_form_initial(self, step):
        """
        🎯 CHARGE les données du chantier à modifier
        Beaucoup plus simple que ma version précédente !
        """
        # Récupère le chantier depuis l'URL
        chantier = Chantier.objects.get(id=self.kwargs['pk'])
        
        # 🎯 Retourne les données selon l'étape
        initial_data = {}
        
        if step == 'info':
            initial_data = {
                'nom_chantier': chantier.nom_chantier,
                'client': chantier.client,
                'reference': chantier.reference,
                'type_travaux': chantier.type_travaux,
                'type_batiment': chantier.type_batiment,
            }
        elif step == 'localisation':
            initial_data = {
                'adresse_chantier': chantier.adresse_chantier,
                'ville_chantier': chantier.ville_chantier,
                'quartier_chantier': chantier.quartier_chantier,
                "pays_chantier" : chantier.pays_chantier,
            }
        elif step == 'caracteristiques':
            initial_data = {
                'surface_totale': chantier.surface_totale,
                'hauteur_batiment': chantier.hauteur_batiment,
                'description_detaille': chantier.description_detaille,
            }
        elif step == 'planning':
            initial_data = {
                'chef_de_chantier': chantier.chef_de_chantier,
                'date_debut_prevue': chantier.date_debut_prevue,
                'date_fin_prevue': chantier.date_fin_prevue,
                'equipe_affectee': chantier.equipe_affectee.all(),
            }
        elif step == 'budget':
            initial_data = {
                'budget_total': chantier.budget_total,
                'cout_materiaux_estime': chantier.cout_materiaux_estime,
                'cout_main_oeuvre_estime': chantier.cout_main_oeuvre_estime,
            }
        
        return initial_data
    
    def done(self, form_list, **kwargs):
        """
        🎯 SAUVEGARDE les modifications
        Presque IDENTIQUE à ta méthode done() !
        """
        # 🎯 Récupère le chantier EXISTANT (seule différence avec Create)
        chantier = Chantier.objects.get(id=self.kwargs['pk'])
        
        # 🎯 COPIER-COLLER de ta méthode done() (ça marche pareil !)
        champs_simples = {}
        equipe_data = None
        
        for form in form_list:
            for field, value in form.cleaned_data.items():
                if value:
                    if field == 'equipe_affectee':
                        equipe_data = value
                    else:
                        champs_simples[field] = value
                        
                
        
        # 🎯 Met à jour le chantier EXISTANT
        for field, value in champs_simples.items():
            setattr(chantier, field, value)
        
        # 🎯 Sauvegarde les modifications
        chantier.save()
        
        # 🎯 Met à jour l'équipe
        if equipe_data:
            chantier.equipe_affectee.set(equipe_data)
            
            chantier.save()
        
        messages.success(self.request, f"✅ Chantier {chantier.nom_chantier} modifié avec succès !")
        
        return redirect('chantier_app:liste-chantier')
   
    
class ChantierDeleteView(LoginRequiredMixin, DeleteView):
    """
    🎯 SUPPRESSION SIMPLE d'un chantier
    """
    model = Chantier
    template_name = 'modal/supprimer_chantier.html'
    success_url = reverse_lazy('chantier_app:liste-chantier')
    
    def get_context_data(self, **kwargs):
        """🎯 Ajoute des infos pour la confirmation"""
        context = super().get_context_data(**kwargs)
        context['title'] = "Confirmer la suppression"
        context['message'] = f"Êtes-vous sûr de vouloir supprimer le chantier '{self.object.nom_chantier}' ?"
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        🎯 Personnalise la suppression avec message
        """
        chantier = self.get_object()
        messages.success(request, f"🗑️ Chantier '{chantier.nom_chantier}' supprimé avec succès")
        return super().delete(request, *args, **kwargs)
    
    
#FILTRER_CHANTIERS_HTMX-Filtre en temps réel avec htmx
def filter_chantiers_htmx(request):
    """Cette vue est appelée par HTMX quand on change un filtre
        Elle retourne Juste la liste des chantiers filtrés
    
    """
    
    # 1. Récupère tous les chantiers
    all_chantiers = Chantier.objects.all()
    
    # 2. on regarde les filter dans l'URL
    #EX: /?status=en_cours&client_id = 5
    
    #Filter par status
    status = request.GET.get('status_chantier') #récupère 'statut du chantier depuis l'URL
    if status:
        chantiers = all_chantiers.filter(status_chantier=status) #Filtre les chantiers par leur status
        
    #Filtre par client
    client_id = request.GET.get("client_id") #récupère 'client_id' depuis l'URL
    if client_id:
        chantiers = all_chantiers.filter(client_id=client_id) #Filtre les chantiers par leur clients
    
    # 3. on retourne JUSTE le html de la liste (pas toute la page)
    return render(request, 'partials/liste_chantier_partial.html',{
        "chantiers": chantiers
    })
    

