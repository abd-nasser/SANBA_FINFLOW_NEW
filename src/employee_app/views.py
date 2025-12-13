from django.views.generic import CreateView, ListView, TemplateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, F, Count
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
        form.instance.status = 'soumis' #Auto_soumission
        
        # Message de succès
        messages.success(self.request,f'Rapport de {form.instance.total_affichage} soumis avec avec succès par {form.instance.employee.username}')
        
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

        context.update(self.get_most_rapport())
        context.update(self.get_total_depense_employee())        
        return context
        
        
    def get_most_rapport(self):
        """L'employé ayant remis le plus de rapport"""
        most_rapport_by_employee = RapportDepense.objects.filter(
            date_creation__year=timezone.now().year,
            date_creation__month=timezone.now().month
            ).values('employee__username').annotate(total_rapports=Count('id')).order_by('-total_rapports')[:1] 
        
        print(most_rapport_by_employee)
          
            
        return {
            'best_employee':most_rapport_by_employee
        }
        
    def get_total_depense_employee(self):
        employee_depense = RapportDepense.objects.filter(
             date_creation__year=timezone.now().year,
            date_creation__month=timezone.now().month
        ).values("employee__username").annotate(
            total_depense =Sum(F("prix_unitaire")*F("quantité"))
            ).order_by("-total_depense")[:1]
        return {
            "total_depense_employee":employee_depense
        }


