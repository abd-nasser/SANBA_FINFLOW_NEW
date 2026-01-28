from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
import django_htmx
from django.db.models import Sum, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from secretaire_app.models import DemandeDecaissement
        
from client_app.forms import ClientForm
from .forms import DemandeDecaissementForm
from .models import DemandeDecaissement
from directeur_app.models import FondDisponible
from auth_app.form import ChangeCredentialsForm


import logging

logger = logging.getLogger(__name__)



def demande_decaissement_view(request):
    fond = get_object_or_404(FondDisponible, id=1)
    list_demande = DemandeDecaissement.objects.all().select_related(
        'demandeur',"chantier","approuve_par"
    ).order_by("-date_demande")[:10]

    if request.method == 'POST':
        try:
            form = DemandeDecaissementForm(request.POST)
            if form.is_valid():
                demande = form.save()
                
                # Après succès d'envoie de demande
                try:
                    send_mail(
                        subject=" Demande Décaissement 💰", 
                        message=f"""Bonjour, Mr {demande.demandeur.username},
                        \n demande un décaissement de {form.cleaned_data.get('montant')} FCFA'
                        \n pour {form.cleaned_data.get("motif")}
                    \n plus d'information : https//sanba/finflow/gestion.org
                    """ ,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=['directeur@gmail.com', "adaneoued@gmail.com","nasserdevtest@gmail.com"]
                    )
                except Exception as e:
                    logger.error(f"Erreur envoi mail demande décaissement {e}")
                                
                
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
            
            try:
            # Après succès
                send_mail(
                    subject=f"💰 Décaissement {decaissement.montant} FCFA",
                    message=f"Décaissement pour {decaissement.demandeur.username}, a été effectué.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[decaissement.demandeur.email, request.user.email,"adaneoued@gmail.com","nasserdevtest@gmail.com"]
                )
            except Exception as e:
                logger.error(f"Erreur envoi mail décaissement {e}")
            
            time_limite = timezone.now() - timedelta(hours=48)
            if decaissement.decaisse==True and decaissement.rapports_depense is None and decaissement.date_decaissement <= time_limite:
                messages.warning(request, f"⚠️ Attention {decaissement.demandeur.username} n'a pas encore soumis son rapport de dépense pour le décaissement, référence:{decaissement.reference_demande} fait il y a plus de 48 heures.")
                
                try:
                    send_mail(
                        subject="⚠️ Rapport de Dépense en Retard",
                        message=f"Bonjour {decaissement.demandeur.username}, n'a pas encore soumis son rapport de dépense pour le décaissement fait il y a plus de 48 heures.",
                        from_email=settings.EMAIL_HOST_USER,    
                        recipient_list=[request.user.email, "nasserdevtest@gmail.com", "adaneoued@gmail.com"]
                    )   
                except Exception as e:
                    logger.error(f"Erreur envoi mail rapport retard {e}")
                
                try:
                    send_mail(
                        subject="⚠️ Rapport de Dépense en Retard",
                        message=f"Bonjour {decaissement.demandeur.username}, vous n'avez pas encore soumis votre rapport de dépense pour le décaissement effectué il y a plus de 48 heures. Veuillez le faire dès que possible.",
                        from_email=settings.EMAIL_HOST_USER,        
                        recipient_list=[decaissement.demandeur.email]
                    )
                except Exception as e:
                    logger.error(f"Erreur envoi mail rapport retard {e}")

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
                Q(demandeur__first_name__icontains=search)|
                Q(demandeur__last_name__icontains=search)|
                Q(chantier__nom_chantier__icontains=search)|
                Q(chantier__reference__icontains=search)|
                Q(motif__icontains=search)|Q(montant__icontains=search)|
                
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
            total_general_refuse = Count('id',filter=Q(status='refusee_directeur') | Q(status="refusee_comptable")),
            total_general_effectue =Sum("montant", filter=Q(decaisse=True))
        )   
        
        queryset = self.get_queryset()
        total_general_filter = queryset.aggregate(total=Sum("montant"))["total"] or 0
        context["total_general_filter"] = total_general_filter
        
        return context
      

