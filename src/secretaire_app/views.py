from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
import django_htmx
from django.db.models import Sum, Count, Q
from django.core.mail import send_mail

from client_app.forms import ClientForm
from .forms import DemandeDecaissementForm
from .models import DemandeDecaissement
from directeur_app.models import FondDisponible
from auth_app.form import ChangeCredentialsForm


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
                
                # Après succès d'envoie de demande
                
                #send_mail(
                    #subject=" Demande Décaissement de ",
                    #message=f"""Bonjour, Mr {demande.demandeur.username},
                    #\n demande un décaissement de {form.cleaned_data.get('montant')} FCFA'
                    #\n pour {form.cleaned_data.get("motif")}
                    #\n plus d'information : https//directeur/directeur-interface.
                    #""" ,
                    #from_email="caisse@sanba.bf",
                    #recipient_list=['directeur@gmail.com', 'comptable@gmail.com']
                #)
                                
                
                return redirect("secretaire_app:secretaire-view")
                
            
            else:
                ctx = {"dmd_form":form,
                       "fond": fond.montant,
                       "ch_form":ChangeCredentialsForm(request.user),
                       "form": ClientForm()
                       }
                return render(request, "secretaire_templates/secretaire.html",ctx)
            
        except Exception as e:
            logger.error(f'erreur {e}')
    
    
    ctx =  {"dmd_form":DemandeDecaissementForm(),
            "list_demande":list_demande,
            "fond": fond.montant,
            "ch_form":ChangeCredentialsForm(request.user),
            "form":ClientForm()
            } 
    return render(request, "secretaire_templates/secretaire.html",ctx)
            
            
            
def valider_decaissement_view(request, decaissement_id):
    
    try:    
        
        fond = FondDisponible.objects.get(id=1)
        decaissement = get_object_or_404(DemandeDecaissement, id=decaissement_id)
        
                 # 🚨 Vérifie pas déjà décaissé
        if decaissement.decaisse:
            messages.warning(request, "⚠️ Déjà décaissé !")
            return redirect("secretaire_app:secretaire-view")
        
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
        
            messages.success(request, f"{request.user} viens de faire le decaissement de  {decaissement.montant} FCFA pour  {decaissement.demandeur.username} ")
            logger.info(f"Décaissement #{decaissement_id}: {decaissement.montant} FCFA -> {decaissement.demandeur.username}")
            
            # Après succès
            #from django.core.mail import send_mail
            #send_mail(
                #subject=f"💰 Décaissement {decaissement.montant} FCFA",
                #message=f"Bonjour {decaissement.demandeur.username}, votre décaissement a été effectué.",
                #from_email="caisse@sanba.bf",
                #recipient_list=[decaissement.demandeur.email, request.user.email]
            #)
                        

    except Exception as e:
        logger.error(f"erreur decaissement {e}")
    return redirect("secretaire_app:secretaire-view")

class HistoriqueDemandeView(LoginRequiredMixin, ListView):
    model = DemandeDecaissement
    template_name="historique/demande_decaissement_hist.html"
    context_object_name = 'dmd_decaissmt_hist'
    
    def get_template_names(self):
        if self.request.headers.get('HX-request'):
            return["partials/filter_demande.html"]
        return[self.template_name]
    
    def get_queryset(self):
        queryset = DemandeDecaissement.objects.all().select_related(
            'demandeur',
            'chantier',
            "approuve_par"
        )
        #################__FILTRER LES DEMANDE PAR STATUS__################################
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        #########################__FILTRER PAR RECHERCHE__############################
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(demandeur__username__icontains=search)|
                Q(demandeur__prenom__icontains=search)|
                Q(approuve_par__post__nom__icontains=search)|
                Q(reference_demande__icontains=search)
            )
        
        return queryset
    
    
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_decaisse"] = DemandeDecaissement.objects.values("demandeur__username").annotate(
                                                            total_decaisse=Sum("montant"),
                                                            nombre_total=Count('id'),
                                                        
                                                            total_approuve =Count("id",filter=Q(decaisse=True)),
                                                            total_refuse=Count('id',filter=Q(decaisse=False))
                                                            ).order_by("-total_decaisse")
        
        context["total_general"]= DemandeDecaissement.objects.aggregate(
            tota_general_decaisse=Sum("montant"),
            total_general_approuve =Count('id',filter=Q(status='approuvee_directeur') | Q(status="approuvee_comptable")),
            total_general_refuse = Count('id',filter=Q(status='refusee_directeur') | Q(status="Refusée par Comptable")),
            total_general_effectue =Sum("montant", filter=Q(decaisse=True))
        )
        
        return context
      

