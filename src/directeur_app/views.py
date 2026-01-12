from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView
from django.db.models import Sum, Count, F, Q, Value, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from decimal import Decimal

from employee_app.models import TypeDepense

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from django.contrib import messages
import logging

from .models import FondDisponible, Historique_dajout_fond
from secretaire_app.models import DemandeDecaissement
from employee_app.models import RapportDepense, Fournisseur
from employee_app.form import ValidationRapportForm, FournisseurForm, RapportDepenseForm, updateRapportFournisseurForm
from auth_app.form import ChangeCredentialsForm, PersonnelRegisterForm


logger = logging.getLogger(__name__)


def directeur_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")[:5]
    
    ctx = {
            "list_demande": list_demande,
            "fond":fond.montant,
            "ch_form":ChangeCredentialsForm(request.user),
            "form":PersonnelRegisterForm()
           }
    return render(request, "directeur_templates/directeur.html", ctx)


def ajouter_fond(request):
    fond = get_object_or_404(FondDisponible, id=1)
    
    if request.method == 'POST':
        try:
            fond_aj = request.POST.get("montant")
            type_depot = request.POST.get("type_depot")
            notes = request.POST.get("notes")
            print(f'Le type de depot est de : {type_depot}')
            fond.montant +=int(fond_aj)
            fond.type_depot = type_depot
            fond.notes = notes
            fond.save()
            historique_de_fond = Historique_dajout_fond.objects.create(nom=request.user, montant=fond_aj,
                                                                       type_depot=type_depot, notes=notes)
            historique_de_fond.save()
            print('Fond ajouté avec succès')
            messages.success(request, f"vous venez d'ajouter la somme de {fond_aj} au fond disponible ! Nouveau Capitale est de : {fond.montant}")
            return redirect("directeur_app:directeur-view")
            
        except Exception as e:
            logger.error(f"error{e}")
            
    return render(request, "directeur_templates/directeur.html", {"fond":fond.montant})

def historique_ajout_fonf(request):
    hist_fond = Historique_dajout_fond.objects.all().order_by('-date_ajout')
    
    # Calcul des stats
    total_ajoutes = hist_fond.aggregate(total=Sum('montant'))['total'] or 0
    moyenne_ajout = total_ajoutes / hist_fond.count() if hist_fond.count() > 0 else 0
    
    # Top contributeurs
   
    top_contributeurs = Historique_dajout_fond.objects.values(
        'nom__username'
    ).annotate(
        total_ajoute=Sum('montant'),
        nb_ajouts=Count('id')
    ).order_by('-total_ajoute')[:3]
    
    context = {
        'hist_fond': hist_fond,
        'total_ajoutes': total_ajoutes,
        'moyenne_ajout': moyenne_ajout,
        'top_contributeurs': top_contributeurs,
    }
    
    return render(request, "historique/hist_fond.html", context)

            
def directeur_approuve_demande_view(request, demande_id):
    demande = get_object_or_404(DemandeDecaissement, id=demande_id)
    
    # MAINTENANT ON PEUT UTILISER request.user.post
    if request.user.is_superuser or request.user.post and request.user.post.nom == "Directeur":
        demande.status = 'approuvee_directeur'
        redirect_name = "directeur_app:directeur-view"
    elif request.user.post and request.user.post.nom == "Comptable":
        demande.status = 'approuvee_comptable'
        redirect_name = "comptable_app:comptable-view"
    else:
        # Si pas de post ou post inconnu
        return redirect("accueil")
    
    demande.approuve_par = request.user
    demande.date_approbation = timezone.now()
    demande.save()
    
    return redirect(redirect_name)

def directeur_refuse_demande_view(request, demande_id):
    demande = get_object_or_404(DemandeDecaissement, id=demande_id)
    
    if  request.user.is_superuser or request.user.post and request.user.post.nom == "Directeur":
        demande.status = 'refusee_directeur'
        redirect_name = "directeur_app:directeur-view"
    elif request.user.post and request.user.post.nom == "Comptable":
        demande.status = 'refusee_comptable'
        redirect_name = "comptable_app:comptable-view"
    else:
        return redirect("accueil")
    
    demande.approuve_par = request.user
    demande.date_approbation = timezone.now()
    demande.save()
    
    return redirect(redirect_name)




class ListRapportDepenseView(LoginRequiredMixin, ListView):
    model= RapportDepense
    template_name = "directeur_templates/rapport_employee.html"
    context_object_name="list_rapport_depense"
    
    def get_template_names(self) -> list[str]:
        if self.request.headers.get('HX-request'):
            return ["partials/rapport_employee_partial.html"]
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
       context =super().get_context_data(**kwargs)
       context["STATUS_RAPPORT_CHOICES"]=RapportDepense.STATUS_RAPPORT_CHOICES
       context['validation_form'] = ValidationRapportForm()
       context["fournisseur_form"] = FournisseurForm()
       context["form"] = updateRapportFournisseurForm()
       context["rapport_soumis"] = RapportDepense.objects.filter(status="soumis").count()
       context["fournisseur"]= RapportDepense.objects.filter(fournisseur__isnull=False).count()
       context["depenses_par_categorie"] =depenses_par_categorie= TypeDepense.objects.filter(
            est_actif=True
            ).values('categorie').annotate(
            total_depenses=Coalesce(
                Sum(F('rapports__prix_unitaire') * F('rapports__quantité'), 
                    filter=Q(rapports__status='valide')),
                Value(Decimal('0')),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).filter(total_depenses__gte=0).order_by('-total_depenses')
              
        
        # Calculer le TOTAL GÉNÉRAL des dépenses validées
       total_general_depenses = Decimal('0')
       for item in depenses_par_categorie:
            total_general_depenses += item['total_depenses'] or Decimal('0')  
            
       context['total_general_depenses']=total_general_depenses
       return context
        
    
    def get_queryset(self):
        queryset= RapportDepense.objects.all().order_by("-date_creation")
        
        #filtrer rapport par status
        status = self.request.GET.get('status')
        if status:
            queryset = RapportDepense.objects.filter(status=status)
        
        #filter par type depense 
        type_depense = self.request.GET.get('type_depense') 
        if type_depense:
            queryset = RapportDepense.objects.filter(type_depense__categorie=type_depense)
            
        #recherche
        search = self.request.GET.get('q')
        if search:
            queryset = RapportDepense.objects.filter(
                Q(demande_decaissement__reference_demande=search)|
                Q(employee__username=search)|
                Q(chantier__nom_chantier=search)|
                Q(chantier__reference=search)     
            )
        return queryset




class ValidationRapportView(LoginRequiredMixin, UpdateView):
    model = RapportDepense
    template_name = "partials\rapport_employee_partial.html"
    context_object_name="rapport"
    form_class = ValidationRapportForm
    success_url = reverse_lazy("directeur_app:rapport-depense-employee")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = "validation_form"
        return context
    def form_valid(self, form):
        return super().form_valid(form)
   

class CreateFournisseurView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    form_class= FournisseurForm
    template_name="modal/ajouter_fournisseur.html"
    success_url = reverse_lazy('directeur_app:rapport-depense-employee')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = "fournisseur_form"
        return context
    
    def form_valid(self, form):
        return super().form_valid(form)
    
class UpdateRapportFournisseurView(LoginRequiredMixin, UpdateView):
    model = RapportDepense
    form_class= updateRapportFournisseurForm
    template_name = "modal/modifier_rapport_fournisseur.html"
    success_url = reverse_lazy('directeur_app:rapport-depense-employee')
    
    
    def form_valid(self, form):
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return super().form_invalid(form)
    
     
    