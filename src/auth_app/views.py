from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from .form import PersonnelRegisterForm
from django.contrib import messages
from auth_app.models import Personnel, Post
from django.contrib.auth.forms import AuthenticationForm
import logging



logger = logging.getLogger(__name__)



def register_view(request):
    if request.method == "POST":
        
        try:
            form = PersonnelRegisterForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f'inscription pour {form.cleaned_data.get("username")}, au post de {form.cleaned_data.get('post')}reussi ')
                return redirect("directeur_app:directeur-view")
                    
            else:
                messages.error(request, "echec l'ors de l'inscription" )
                return render(request, "auth_templates/register.html", {"form":form})
            
        except Exception as e:
            logger.error(f"erreur {e}")
             
    return render(request, "auth_templates/register.html", {"form":PersonnelRegisterForm()})



def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()  # Ici user EST déjà un Personnel (car tu utilises Personnel comme User)
            login(request, user)
            
            # MAINTENANT on peut rediriger selon le poste
            if user.is_superuser or user.post.nom == "Directeur":
                return redirect("directeur_app:directeur-view")
            
            elif user.post.nom == "Comptable":
                return redirect("comptable_app:comptable-view")
            
            elif user.post.nom == "Secretaire":
                return redirect("secretaire_app:secretaire-view")
            
            elif user.post.nom == "Employee":
                return redirect("employee_app:employee-view")
            
            else:
                # Poste non reconnu - dashboard par défaut
                return redirect("dashboard:default")
        
        else:
            # Formulaire invalide
            return render(request, "auth_templates/login.html", {"form": form})
    
    # GET request
    return render(request, "auth_templates/login.html", {"form": AuthenticationForm()})



def logout_view(request):
    logout(request)
    return redirect("auth_app:login")
    