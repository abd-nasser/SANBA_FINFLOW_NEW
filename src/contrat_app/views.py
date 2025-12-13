from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView,  UpdateView, DetailView, DeleteView


from .models import Contrat
from .forms import ContratForm


class ContratView(LoginRequiredMixin, ListView):
    model = Contrat
    template_name = 'contrat_templates/list_contrat.html'
    context_object_name = "contrats"
    
    
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
    template_name='contrat_templates/detail_contrat.html'
    context_object_name = 'contrat'
    
    

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