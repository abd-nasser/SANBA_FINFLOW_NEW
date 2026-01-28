from django.utils import timezone
from django.shortcuts import render
from auth_app.form import ChangeCredentialsForm
from auth_app.form import PersonnelRegisterForm
from django.shortcuts import render, get_object_or_404, redirect
from directeur_app.models import FondDisponible, Historique_dajout_fond
from secretaire_app.models import DemandeDecaissement
from employee_app.models import RapportDepense
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def comptable_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().select_related(
        "demandeur", "chantier", "approuve_par",).order_by("-date_demande")[:5]
    # list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")[:5]
    
    ctx = {
            "list_demande": list_demande,
            "fond":fond.montant,
            "ch_form":ChangeCredentialsForm(request.user),
            "form":PersonnelRegisterForm()
           }
    return render(request, "comptable_templates/comptable.html", ctx)



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
            return redirect("comptable_app:comptable-view")
            
        except Exception as e:
            logger.error(f"error{e}")
            
    return render(request, "partials/ajouter_fond.html")
            
        
def comptable_approuve_demande_view(request, demande_id):
    demande = get_object_or_404(DemandeDecaissement, id=demande_id)
    
    # MAINTENANT ON PEUT UTILISER request.user.post
    if request.user.is_superuser or request.user.post  and request.user.post.nom == "Directeur":
        demande.status = 'approuvee_directeur'
        redirect_name = "directeur_app:directeur-view"
    elif request.user.post and request.user.post.nom == "Comptable":
        demande.status = 'approuvee_comptable'
        redirect_name = "comptable_app:comptable-view"
    else:
        # Si pas de post ou post inconnu
        return redirect("auth_app:login")
    
    demande.approuve_par = request.user
    demande.date_approbation = timezone.now()
    demande.save()
    
    return redirect(redirect_name)

def comptable_refuse_demande_view(request, demande_id):
    demande = get_object_or_404(DemandeDecaissement, id=demande_id)
    
    if  request.user.is_superuser or request.user.post and request.user.post.nom == "Directeur":
        demande.status = 'refusee_directeur'
        redirect_name = "directeur_app:directeur-view"
    elif  request.user.is_superuser or request.user.post and request.user.post.nom == "Comptable":
        demande.status = 'refusee_comptable'
        redirect_name = "comptable_app:comptable-view"
    else:
        return redirect("auth_app:login")
    
    demande.approuve_par = request.user
    demande.date_approbation = timezone.now()
    demande.save()
    
    return redirect(redirect_name)


def list_rapport_depense_view(request):
    list_rapport_depense = RapportDepense.objects.all().order_by("-date")
    ctx = {"list_rapport_depense":list_rapport_depense}
    return render(request, "directeur_templates/rapport_employee.html", ctx)