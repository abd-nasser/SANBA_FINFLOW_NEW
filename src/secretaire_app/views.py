from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .forms import DemandeDecaissementForm
from .models import DemandeDecaissement
from directeur_app.models import FondDisponible


import logging

logger = logging.getLogger(__name__)



def demande_decaissement_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")
    
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
            decaissement.status="decaisse"
            decaissement.date_decaissement = timezone.now()
            decaissement.save()
            fond.save()
        
            messages.success(request, f"vous venez de faire le decaissement de la somme {decaissement.montant}")
    except Exception as e:
        logger.error(f"erreur decaissement {e}")
    return redirect("secretaire_app:secretaire-view")