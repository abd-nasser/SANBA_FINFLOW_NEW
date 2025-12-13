from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
import django_htmx
from django.db.models import Sum, Count, Q



from .forms import DemandeDecaissementForm
from .models import DemandeDecaissement
from directeur_app.models import FondDisponible


import logging

logger = logging.getLogger(__name__)



def demande_decaissement_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")[:3]
    
    if request.method == 'POST':
        try:
            form = DemandeDecaissementForm(request.POST)
            if form.is_valid():
                demande = form.save()
                return redirect("secretaire_app:secretaire-view")
                
            
            else:
                ctx = {"form":form,
                       "fond": fond.montant}
                return render(request, "secretaire_templates/secretaire.html",ctx)
            
        except Exception as e:
            logger.error(f'erreur {e}')
    
    
    ctx =  {"form":DemandeDecaissementForm(),
            "list_demande":list_demande,
            "fond": fond.montant} 
    return render(request, "secretaire_templates/secretaire.html",ctx)
            
def valider_decaissement_view(request, decaissement_id):
    try:
        fond = FondDisponible.objects.get(id=1)
        decaissement = get_object_or_404(DemandeDecaissement, id=decaissement_id)
        if fond.montant < decaissement.montant:
            messages.info(request, "Fond inssufisant")
            
        elif decaissement.montant <= 0 or decaissement.montant==None:
            messages.info(request, "Impossible veillez verifier la somme")
        else:
            fond.montant -= decaissement.montant
            decaissement.decaisse = True
            decaissement.date_decaissement = timezone.now()
            decaissement.save()
            fond.save()
        
            messages.success(request, f"vous venez de faire le decaissement de la somme {decaissement.montant}")
    except Exception as e:
        logger.error(f"erreur decaissement {e}")
    return redirect("secretaire_app:secretaire-view")

class HistoriqueDemandeView(LoginRequiredMixin, ListView):
    model = DemandeDecaissement
    template_name="historique/demande_decaissement_hist.html"
    context_object_name = 'dmd_decaissmt_hist'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_decaisse"] = DemandeDecaissement.objects.values("nom__username").annotate(
                                                            total_decaisse=Sum("montant"),
                                                            nombre_total=Count('id'),
                                                        
                                                            total_approuve =Count("id",filter=Q(decaisse=True)),
                                                            total_refuse=Count('id',filter=Q(decaisse=False))
                                                            ).order_by("-total_decaisse")
        
        return context
     

def filter_demande_decaisse(request):
    print("sa au moin")
    value = request.GET.get("status")
    print("requet fait")
    demande_by_status = DemandeDecaissement.objects.filter(status=value).order_by('-date_demande')
    for dmd in demande_by_status:
            print(dmd.nom)
            print(dmd.montant)
            print(dmd.status)
    ctx = {'dmd_decaissmt_hist':demande_by_status}
    return render(request, "partials/filter_demande.html",ctx)