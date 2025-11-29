from django.contrib import messages
from django.shortcuts import redirect, render
from .form import RapportDepenseForm
from .models import RapportDepense


def rapport_depense_view(request):
    
    if request.method == "POST":
        form = RapportDepenseForm(request.POST, request.FILES)
        if form.is_valid():
            rapport = form.save(commit=False)
            rapport.employee = request.user
            rapport.save()
            messages.success(request, "Rapport de dépense enregistré avec succès.")
            redirect("employee_app:employee-view")
        else:
            messages.error(request, "Erreur lors de l'enregistrement du rapport de dépense.")
            return render(request, "employee_templates/employee.html", {"form":form})
        print("rapport save")
    ctx = {"form":RapportDepenseForm()}
    return render(request, "employee_templates/employee.html", ctx)
    
        
        
        
        
        
        
        
