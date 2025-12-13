from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from django.contrib import messages
import logging

from .models import FondDisponible, Historique_dajout_fond
from secretaire_app.models import DemandeDecaissement
from employee_app.models import RapportDepense, Fournisseur
from employee_app.form import ValidationRapportForm, FournisseurForm, RapportDepenseForm, updateRapportFournisseurForm



logger = logging.getLogger(__name__)


def directeur_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")
    
    ctx = {
            "list_demande": list_demande,
            "fond":fond.montant,
           }
    return render(request, "directeur_templates/directeur.html", ctx)


def ajouter_fond(request):
    fond = get_object_or_404(FondDisponible, id=1)
    
    if request.method == 'POST':
        try:
            fond_aj = request.POST.get("montant")
            fond.montant +=int(fond_aj)
            fond.save()
            historique_de_fond = Historique_dajout_fond.objects.create(nom=request.user, montant=fond_aj)
            historique_de_fond.save()
            print('Fond ajouté avec succès')
            messages.success(request, f"vous venez d'ajouter la somme de {fond_aj} au fond disponible ! Nouveau Capitale est de : {fond.montant}")
            return redirect("directeur_app:directeur-view")
            
        except Exception as e:
            logger.error(f"error{e}")
            
    return render(request, "modal/ajouter_fond.html")

            
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


def list_rapport_depense_view(request):
    list_rapport_depense = RapportDepense.objects.all().order_by("-date_creation")
    ctx = {"list_rapport_depense":list_rapport_depense}
    return render(request, "directeur_templates/rapport_employee.html", ctx)


class ValidationRapportView(LoginRequiredMixin, UpdateView):
    model = RapportDepense
    template_name = 'directeur_templates/rapport_employee.html'
    form_class = ValidationRapportForm
    success_url = reverse_lazy("directeur_app:rapport-depense-employee")
    
    def form_valid(self, form):
        return super().form_valid(form)
   

class CreateFournisseurView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    form_class= FournisseurForm
    template_name="modal/ajouter_fournisseur.html"
    success_url = reverse_lazy('directeur_app:rapport-depense-employee')
    
    def form_valid(self, form):
        return super().form_valid(form)
    
class UpdateRapportFournisseurView(LoginRequiredMixin, UpdateView):
    model = RapportDepense
    form_class= updateRapportFournisseurForm
    template_name = "modal/modifier_rapport_fournisseur.html"
    success_url = reverse_lazy('directeur_app:rapport-depense-employee')
    
    def form_valid(self, form):
        print('fait')
        return super().form_valid(form)
    def form_invalid(self, form):
        print('infait')
        return super().form_invalid(form)
    
    