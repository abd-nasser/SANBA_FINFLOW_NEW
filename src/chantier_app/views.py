from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView , DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.utils import timezone
from chantier_app import models
from django.db.models import Q, Sum, F
from django.contrib.auth.decorators import login_required

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
    
    def get_template_names(self):
        """retourne le template partial si requete HTMX"""
        if self.request.headers.get('HX-request'):
            #si requet HTMX ->  retourne slmt te tableau (pas toute la page)
            return["partials/liste_chantier_partial.html"]
        
        #requet normale -> retourne la page complète
        return [self.template_name]
        
    def get_queryset(self):
       """FILTRAGE INTELLIGENT AVEC OPTIMISATION DB"""
       #OPTIMISATION CRITIQUE: select_related
       queryset = Chantier.objects.all().select_related(
           'client',
           'chef_de_chantier'
           
        # ⚡ AVANT : 1 requête par chantier pour client + 1 par chef
        # ⚡ APRÈS : 1 seule requête avec JOIN pour TOUS les chantiers
           
       ).prefetch_related('equipe_affectee')
       # ⬅️ ManyToMany : Charge TOUTE l'équipe en 2 requêtes max
       # 1. Tous les chantiers
       # 2. Tous les équipes de ces chantiers
       # ❌ SANS ça : 1 requête par chantier pour l'équipe !
        
       ########################__ 1️⃣ FILTRE STATUT (le plus important) __############################
       status = self.request.GET.get('status') #recupère depuid URL ? status=en_cours
       if status:
           if status == 'retard':
               #Cas spécial : chantiers "en_cours" + date dépassée
               queryset = queryset.filter(
                   status_chantier="en_cours",
                   date_fin_prevue=timezone.now().date()
                   
               )
           else:
               queryset= queryset.filter(status_chantier=status)
        
       #########################__ # 2️⃣ FILTRE TYPE TRAVAUX __############################
       type_travaux = self.request.GET.get("type_travaux") 
       if type_travaux:
           queryset = Chantier.objects.filter(type_travaux=type_travaux)
           
       ########################__ # 3️⃣ RECHERCHE TEXTE (nom chantier Ou client) __############################
       search_query =  self.request.GET.get('q') #q pour query standars
       if search_query:
           #Q()= OR condition (cherche dans plusieurs champs)
           queryset = queryset.filter(
               Q(nom_chantier__icontains=search_query)|
               Q(client__nom__icontains=search_query)|
               Q(client__prenom__icontains=search_query)|
               Q(client__raison_sociale__icontains=search_query)|
               Q(reference__icontains=search_query)
           )
        
       return queryset.order_by('-date_creation')
   
    def get_context_data(self, **kwargs):
        """AJOUTE DES Données UTILES au Template"""
        context = super().get_context_data(**kwargs) #Récupère le contexte de base
        
        #STATS pour affichage(en-tete, badges)
        context['total_chantiers'] = self.get_queryset().count()
        #compte tous les chantiers filtres
        context['chantiers_en_cours'] = self.get_queryset().filter(
            status_chantier="en_cours"
        ).count()
        
        context['chantiers_termines'] = self.get_queryset().filter(
            status_chantier="termine"
        ).count()
        
        context['chantiers_paye'] = self.get_queryset().filter(
            status_chantier="paye"
        ).count()
        context['chantiers_en_retard']=self.get_queryset().filter(
            status_chantier='en_cours',
            date_fin_prevue__lt=timezone.now().date()
        ).count()
        #compte slmt ceux en retard
        
        #OPTIONS pour les selects html
        context['STATUS_CHANTIER_CHOICES']=Chantier.STATUS_CHANTIER_CHOICES
        #EX: [('en_cours', 'En cours'), ('termine', 'Terminé')...]
        
        context['TYPE_TRAVAUX_CHOICES']=Chantier.TYPE_TRAVAUX_CHOICES
        
        return context # Retourne tout au template
          
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
        context = super().get_context_data(**kwargs)
        chantier = self.get_object() #le chantier actuel
        #Ajoute des données supplémentaires
        context['total_depenses'] = chantier.depenses.aggregate(
            total = Sum(F('prix_unitaire') * F('quantité'))
        )["total"] or 0
       
        return context
        

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
    

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone


@login_required
def planifier_chantier_view(request, chantier_id):
    """Remet un chantier en planification (change son status à 'planification')"""
    try:
        chantier = get_object_or_404(Chantier, pk=chantier_id)
    
        # Vérifier si le chantier peut être replanifié
        if chantier.status_chantier == 'annule':
            messages.error(request, f"❌ Impossible de replanifier le chantier '{chantier.nom_chantier}' car il est annulé.")
        elif chantier.status_chantier == 'termine':
            messages.error(request, f"❌ Impossible de replanifier le chantier '{chantier.nom_chantier}' car il est déjà terminé.")
        elif chantier.status_chantier == 'planification':
            messages.info(request, f"ℹ️ Le chantier '{chantier.nom_chantier}' est déjà en planification.")
        else:
            # Remettre en planification
            chantier.status_chantier = "planification"
            chantier.date_debut_reelle = None  # Réinitialiser la date de début
            chantier.date_modification = timezone.now()
            chantier.save()
            
            messages.info(request, f"📋 Le chantier '{chantier.nom_chantier}' a été remis en planification.")
        
        return redirect("chantier_app:detail-chantier", pk=chantier.id)
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la replanification du chantier: {str(e)}")
        return redirect("chantier_app:liste-chantier")
    


@login_required
def commencer_chantier_view(request, chantier_id):
    """Démarre un chantier (change son status à 'en_cours')"""
    try:
        chantier = get_object_or_404(Chantier, pk=chantier_id)
        
        # Vérifier si le chantier peut être démarré
        if chantier.status_chantier == 'termine':
            messages.error(request, f"❌ Impossible de démarrer le chantier '{chantier.nom_chantier}' car il est déjà terminé.")
        elif chantier.status_chantier == 'annule':
            messages.error(request, f"❌ Impossible de démarrer le chantier '{chantier.nom_chantier}' car il est annulé.")
        elif chantier.status_chantier == 'en_cours':
            messages.info(request, f"ℹ️ Le chantier '{chantier.nom_chantier}' est déjà en cours.")
        else:
            # Démarrer le chantier
            chantier.status_chantier = "en_cours"
            chantier.date_debut_reelle = timezone.now().date()
            chantier.date_modification = timezone.now()
            chantier.save()
            
            messages.success(request, f"✅ Le chantier '{chantier.nom_chantier}' a été démarré avec succès!")
        
        # Rediriger vers le détail du chantier avec le paramètre
        return redirect("chantier_app:detail-chantier", pk=chantier.id)
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors du démarrage du chantier: {str(e)}")
        return redirect("chantier_app:liste-chantier")
    
    
@login_required
def terminer_chantier_view(request, chantier_id):
    """Termine un chantier (change son status à 'termine')"""
    try:
        chantier = get_object_or_404(Chantier, pk=chantier_id)
        
        # Vérifier si le chantier peut être terminé
        if chantier.status_chantier == 'annule':
            messages.error(request, f"❌ Impossible de terminer le chantier '{chantier.nom_chantier}' car il est annulé.")
        elif chantier.status_chantier == 'termine':
            messages.info(request, f"ℹ️ Le chantier '{chantier.nom_chantier}' est déjà terminé.")
        elif chantier.status_chantier not in ['en_cours', 'suspendu']:
            messages.error(request, f"❌ Le chantier '{chantier.nom_chantier}' doit être en cours ou suspendu pour être terminé.")
        else:
            # Terminer le chantier
            chantier.status_chantier = "termine"
            chantier.date_fin_reelle = timezone.now().date()
            chantier.date_modification = timezone.now()
            chantier.save()
            
            messages.success(request, f"✅ Le chantier '{chantier.nom_chantier}' a été terminé avec succès!")
        
        return redirect("chantier_app:detail-chantier", pk=chantier.id)
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la terminaison du chantier: {str(e)}")
        return redirect("chantier_app:liste-chantier")


@login_required
def suspendre_chantier_view(request, chantier_id):
    """Suspend un chantier (change son status à 'suspendu')"""
    try:
        chantier = get_object_or_404(Chantier, pk=chantier_id)
        
        # Vérifier si le chantier peut être suspendu
        if chantier.status_chantier == 'annule':
            messages.error(request, f"❌ Impossible de suspendre le chantier '{chantier.nom_chantier}' car il est annulé.")
        elif chantier.status_chantier == 'termine':
            messages.error(request, f"❌ Impossible de suspendre le chantier '{chantier.nom_chantier}' car il est déjà terminé.")
        elif chantier.status_chantier == 'suspendu':
            messages.info(request, f"ℹ️ Le chantier '{chantier.nom_chantier}' est déjà suspendu.")
        elif chantier.status_chantier != 'en_cours':
            messages.error(request, f"❌ Le chantier '{chantier.nom_chantier}' doit être en cours pour être suspendu.")
        else:
            # Suspendre le chantier
            chantier.status_chantier = "suspendu"
            chantier.date_modification = timezone.now()
            chantier.save()
            
            messages.warning(request, f"⚠️ Le chantier '{chantier.nom_chantier}' a été suspendu.")
        
        return redirect("chantier_app:detail-chantier", pk=chantier.id)
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la suspension du chantier: {str(e)}")
        return redirect("chantier_app:liste-chantier")
    

@login_required
def annuler_chantier_view(request, chantier_id):
    """Annule un chantier (change son status à 'annule')"""
    try:
        chantier = get_object_or_404(Chantier, pk=chantier_id)
        
        # Vérifier si le chantier peut être annulé
        if chantier.status_chantier == 'annule':
            messages.info(request, f"ℹ️ Le chantier '{chantier.nom_chantier}' est déjà annulé.")
        elif chantier.status_chantier == 'termine':
            messages.error(request, f"❌ Impossible d'annuler le chantier '{chantier.nom_chantier}' car il est déjà terminé.")
        else:
            # Annuler le chantier
            ancien_status = chantier.status_chantier
            chantier.status_chantier = "annule"
            chantier.date_modification = timezone.now()
            chantier.save()
            
            messages.error(request, f"❌ Le chantier '{chantier.nom_chantier}' a été annulé (ancien statut: {ancien_status}).")
        
        return redirect("chantier_app:detail-chantier", pk=chantier.id)
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de l'annulation du chantier: {str(e)}")
        return redirect("chantier_app:liste-chantier")
    

def get_status_modal(request, chantier_id):
    """Vue pour charger le modal de changement de statut"""
    chantier = get_object_or_404(Chantier, id=chantier_id)
    return render(request, 'modal/status_chantier.html', {'chantier': chantier})