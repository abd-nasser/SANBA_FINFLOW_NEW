from django.views.generic import CreateView, ListView, TemplateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, F, Count, Q
from django.urls import reverse_lazy

from .form import RapportDepenseForm, FiltreRapportForm, FournisseurForm
from .models import RapportDepense, Fournisseur
from auth_app.models import Personnel

class CreerRapportDepenseView(LoginRequiredMixin, CreateView):
    """Vue pour créer les rapport de dépense"""
    model = RapportDepense
    form_class = RapportDepenseForm
    template_name = "employee_templates/creer_rapport.html"
    success_url = reverse_lazy('employee_app:mes-rapports')
    
    def get_form_kwargs(self):
        """Passe l'employé connecté au formulaire"""
        kwargs =super().get_form_kwargs()
        kwargs['employee'] = self.request.user
        return kwargs
    
    
    def form_valid(self, form):
        """Associe l'employé automatiquement"""
        form.instance.employee = self.request.user
        form.instance.status = 'soumis'
        
        # Message amélioré avec le lien
        if form.instance.demande_decaissement:
            messages.success(self.request,
                f'Rapport de {form.instance.total_affichage} soumis '
                f'pour la demande "{form.instance.demande_decaissement.motif}"')
        else:
            messages.success(self.request,
                f'Rapport de {form.instance.total_affichage} soumis '
                f'(sans lien avec une demande)')
        
        return super().form_valid(form)
            
            
class MesRapportsView(LoginRequiredMixin, ListView):

    """Vue pour voir ses propres rapports"""
    model = RapportDepense
    template_name='employee_templates/mes_rapports.html'
    context_object_name = 'rapports'
    paginate_by = 10
    
    def get_queryset(self):
        """Filtre les rapports de l'employee connecté"""
        
        #queryset des rapports par l'employéé connecter
        queryset = RapportDepense.objects.filter(
            employee=self.request.user
        ).select_related('type_depense','chantier', 'fournisseur')
        
        # Applique les filtres du formulaire
        form = FiltreRapportForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('date_debut'):
                queryset = queryset.filter(date_depense__gte=form.cleaned_data["date_debut"])
                
            if form.cleaned_data.get('date_fin'):
                queryset = queryset.filter(date_depense__lte=form.cleaned_data['date_fin'])
            
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data.get('type_depense'):
                queryset = queryset.filter(type_depense=form.cleaned_data['type_depense'])
            
            if form.cleaned_data.get('chantier'):
                queryset = queryset.filter(chantier=form.cleaned_data["chantier"])
        
        return queryset.order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        """Ajoute le formulaire de filtre"""
        context = super().get_context_data(**kwargs)
        context['filter_form']=FiltreRapportForm(self.request.GET)
        
        #Stats rapides
        context['total_depenses'] = self.get_queryset().aggregate(
            total =Sum(F('prix_unitaire')*F('quantité'))
        )["total"] or 0
        
        return  context
                
    
    
class BestEmployeeView(LoginRequiredMixin,TemplateView):
    template_name = "employee_du_mois.html"  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_employe_performant())        
        return context
        
        
       
    def get_employe_performant(self):
        employee_depense = RapportDepense.objects.filter(
             date_creation__year=timezone.now().year,
            date_creation__month=timezone.now().month,
            status="valide"
        ).values("employee__username").annotate(
            total_depense =Sum(F("prix_unitaire")*F("quantité"))
            ).order_by("-total_depense")[:1]
        
        top_commerciaux = Personnel.objects.values("username").annotate(
            clients_amenes= Count('clients_attaches'),
            chantier_status_en_cours= Count('clients_attaches__chantiers', filter=Q(clients_attaches__chantiers__status_chantier='en_cours')),
            chantier_status_termine= Count('clients_attaches__chantiers', filter=Q(clients_attaches__chantiers__status_chantier='termine')),
            contrats_signes= Count('clients_attaches__chantiers__contrats'),
            ca_genere= Sum('clients_attaches__chantiers__contrats__montant_total')
        ).exclude(ca_genere=None).order_by('-ca_genere')[:1]
    

        most_rapport_by_employee = RapportDepense.objects.filter(
            date_creation__year=timezone.now().year,
            date_creation__month=timezone.now().month
            ).values('employee__username').annotate(total_rapports=Count('id')).order_by('-total_rapports')[:1] 
        
             
        return {
            "total_depense_employee":employee_depense,
            "rapports_employee":most_rapport_by_employee,
            'top_commerciaux':top_commerciaux
        }   


