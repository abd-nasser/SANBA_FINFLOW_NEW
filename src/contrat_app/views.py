from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView,  UpdateView, DetailView, DeleteView
from django.db.models import Q

from .models import Contrat
from .forms import ContratForm


class ContratView(LoginRequiredMixin, ListView):
    model = Contrat
    template_name = 'contrat_templates/list_contrat.html'
    context_object_name = "contrats"
    
    def get_template_names(self) -> list[str]:
        """ retourne le template partials si requete HTMX """
        if self.request.headers.get('HX-request'):
            # si requet HTMX -> retourne slmt le tableau(pas toute la page)
            return ["partials/liste_contrat_partial.html"]
        # requet normale -> retourne la page complète
        return[self.template_name]
    
    
    def get_queryset(self):
        """FILTRAGE INTELLIGENT AVEC OPTIMASATION"""
        #OPTIMISATION CRITIQUE: select_related
        queryset = Contrat.objects.all().select_related(
            'chantier'
        )
        #########################__RECHERCHE DE CONTRAT PAR NON CHANTIER__###########################
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(chantier__nom_chantier__icontain=search_query)|
                Q(reference_contrat__icontains=search_query)
            )
        return  queryset
    
    
    
class createContratView(LoginRequiredMixin, CreateView):
    model = Contrat
    form_class = ContratForm
    template_name='modal/ajouter_contrat.html'
    success_url = reverse_lazy("contrat_app:liste-contrats")
    
    def form_valid(self, form):
        return super().form_valid(form)
    
class ContratUpdateView(LoginRequiredMixin, UpdateView):
    model= Contrat
    form_class = ContratForm
    template_name='modal/modifier_contrat.html'
    success_url = reverse_lazy("contrat_app:liste-contrats")
    
    def form_valid(self, form):
        return super().form_valid(form)
    

class ContratDetaiView(LoginRequiredMixin, DetailView):
    model = Contrat
    chantier = Contrat.chantier
    context_object_name= "contrat"
    
    def get_template_names(self) -> list[str]:
        if self.chantier.type_travaux in ['decoration']:
            return ["contrat_templates/detail_contrat_deco.html"]
        elif self.chantier.type_travaux in ['toiture_tole', 'toiture_couverture', 'toiture_etancheite']:
            return ["contrat_templates/detail_contrat_toiture.html"]
        
        else:
            return ["contrat_templates/detail_contrat.html"]
        
    

    
    

class ContratDeleteView(LoginRequiredMixin, DeleteView):
    model = Contrat
    template_name ='modal/supprimer_contrat.html'
    success_url = reverse_lazy("contrat_app:liste-contrats")
    
    def delete(self, request, *args, **kwargs):
        contrat = self.get_object()
        messages.success(self.request, f"suppression du contrat {contrat.reference_contrat} reussi")
        return super().delete(request, *args, **kwargs)
    

def enregister_paiement_view(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    if request.method == "POST":
        nouveau_paiement = request.POST.get('nouveau-paiement')
        contrat.enregistrer_paiement(int(nouveau_paiement))
        contrat.save()
        return redirect("contrat_app:detail-contrat", pk=contrat_id)
    return render(request, 'modal/enregistrer_paiement.html', {'contrat':contrat})