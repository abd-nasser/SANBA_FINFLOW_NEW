from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from .form import PersonnelRegisterForm, ChangeCredentialsForm
from django.contrib import messages
from auth_app.models import Personnel, Post
from django.contrib.auth.forms import AuthenticationForm
from directeur_app.models import FondDisponible
from secretaire_app.models import DemandeDecaissement
from secretaire_app.forms import DemandeDecaissementForm
from client_app.forms import ClientForm
from employee_app.form import RapportDepenseForm
from django.core.mail import send_mail
from django.conf import settings
import logging



logger = logging.getLogger(__name__)



def register_view(request):
    if request.method == "POST":
        try:
            # Utiliser ModelForm si tu changes
            form = PersonnelRegisterForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                # Générer username
                first = form.cleaned_data['first_name'][0].lower()
                last = form.cleaned_data['last_name'].lower().replace(" ", "")
                base_username = f"{first}{last}"
                
                username = base_username
                counter = 1
                while Personnel.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Générer mot de passe
                import secrets
                alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                password = ''.join(secrets.choice(alphabet) for _ in range(10))
                
                # Créer l'utilisateur Personnel
                user = Personnel.objects.create_user(
                    username=username,
                    password=password,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    post=form.cleaned_data['post'],
                    telephone=form.cleaned_data['telephone'],
                    date_de_naissance=form.cleaned_data['date_de_naissance'],
                    lieu_de_naissance=form.cleaned_data['lieu_de_naissance'],
                    personne_a_prevenir_en_cas=form.cleaned_data['personne_a_prevenir_en_cas']
                )
                send_mail(
                    subject="Identifiant Temporaire",
                    message=f"""Bonjour, Mr/Mme {form.cleaned_data.get('first_name')},
                    \n Vos identifiant pour SANBA GESTION FINFLOW: 
                    \n nom d'utilisateur = {username}
                    \n mot de passe = {password}
                    \n Ces informations sont à titre personnel,
                    \n Veuillez les garder en sécurité et privée
                    """ ,
                    from_email=settings.EMAIL_HOST_USER, #sender email defini at setting.py 
                    fail_silently=False,
                    recipient_list=[email]
                )
                
                messages.success(request, 
                    f"✅ {user.get_full_name()} inscrit(e)!\n"
                    f"👤 Login: {username}\n"
                    f"🔐 MDP: {password}")
                
                return redirect("directeur_app:directeur-view")
            
            else:
                # Préserver le contexte directeur
                fond = get_object_or_404(FondDisponible, id=1)
                list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")
                
                ctx = {
                    "list_demande": list_demande,
                    "fond":fond.montant,
                    "form": form,
                    "ch_form":ChangeCredentialsForm(user=request.user),
                    "open_register_modal": True}
                
                response = render(request, "directeur_templates/directeur.html", ctx)
                response['HX-Trigger'] = 'registerFailed'
                return response
                
        except Exception as e:
            logger.error(f"Erreur inscription: {e}")
            messages.error(request, "❌ Erreur lors de l'inscription")
    
    return render(request, "directeur_templates/directeur.html", {"form": PersonnelRegisterForm()})



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
            
            elif user.post.nom == "Sécretaire":
                return redirect("secretaire_app:secretaire-view")
            
            elif user.post.nom == "Employé":
                return redirect("employee_app:employee-view")
            
            else:
                # Poste non reconnu - dashboard par défaut
                return redirect("auth_app:login")
        
        else:
            # Formulaire invalide — rendre la page avec un flag pour rouvrir le modal
            response = render(request, "home.html", {"form": form, "open_login_modal": True})
            # Si la requête provient d'HTMX, déclencher aussi l'événement côté client
            response['HX-Trigger'] = 'loginFailed'
            return response
    
    # GET request
    return render(request, "home.html", {"form": AuthenticationForm()})


def change_credentials_view(request):
    if request.method == 'POST':
        form = ChangeCredentialsForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            
            #change username si fourni
            new_username = form.cleaned_data.get("new_username")
            if new_username:
                if Personnel.objects.filter(username=new_username).exclude(id=user.id).exists():
                    messages.error(request, "ce nom d'utilisateur est déjà pris")
                else:
                    user.username = new_username
                    messages.success(request, f"nom d'utilisateur changé en: {new_username}")
                    
            #change password si fourni
            new_password = form.cleaned_data.get("new_password")
            if new_password:
                print(f"new_password: {new_password}")
                print(f"new_username: {new_username}")
                user.set_password(new_password)
                
                send_mail(
                    subject="Identifiant Temporaire",
                    message=f"""Bonjour, Mr/Mme {request.user.last_name},
                    \n Vous venez de changer vos identifiant pour SANBA GESTION FINFLOW: 
                    \n nouveau nom d'utilisateur = {new_username}
                    \n  nouveau mot de passe = {new_password}
                    \n Ces informations sont à titre personnel,
                    \n Veuillez les garder en sécurité et privée
                    """ ,
                    from_email=settings.EMAIL_HOST_USER, #sender email defini at setting.py 
                    fail_silently=False,
                    recipient_list=[request.user.email]
                )
                messages.success(request, "Mot de pass changé avec succès")
                
                
            user.save()
            
            #Ré-authentifier si mot de passe changé
            if new_password:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                if request.user.is_superuser or request.user.post.nom == "Directeur":
                    return redirect("directeur_app:directeur-view")
                
                elif request.user.post.nom == "Comptable":
                    return redirect("comptable_app:comptable-view")
                
                elif request.user.post.nom == "Sécretaire":
                    return redirect("secretaire_app:secretaire-view")
                
                elif request.user.post.nom == "Employé":
                    return redirect("employee_app:employee-view")
            
                else:
                    # Poste non reconnu - dashboard par défaut
                    return redirect("home_app:home-view")
        else:
            
                    # Préserver le contexte directeur
            fond = get_object_or_404(FondDisponible, id=1)
            list_demande = DemandeDecaissement.objects.all().order_by("-date_demande")
            
            ctx = {
                "list_demande": list_demande,
                "fond": fond.montant,
                "ch_form": form,  # Le form avec erreurs
                "form": PersonnelRegisterForm(),
                "dmd_form":DemandeDecaissementForm(),
                "rapport_form":RapportDepenseForm(),
                "open_change_id": True
            }
            
            if request.user.post.nom == "Directeur" or request.user.is_superuser:
                response = render(request, "directeur_templates/directeur.html", ctx)
                response["HX-Trigger"] ="failed_change_id"
                return response
            
            elif request.user.post.nom == "Sécretaire":
                response = render(request, "secretaire_templates/secretaire.html",{
                "list_demande": list_demande,
                "fond": fond.montant,
                "ch_form": form,  # Le form avec erreurs
                "form": ClientForm(),
                "dmd_form":DemandeDecaissementForm(),
                "rapport_form":RapportDepenseForm(),
                "open_change_id": True
            })
                response["HX-Trigger"] ="failed_change_id"
                return response
            
            elif request.user.post.nom == "Comptable":
                response = render(request, "comptable_templates/comtable.html",{
                "list_demande": list_demande,
                "fond": fond.montant,
                "ch_form": form,  # Le form avec erreurs
                "form": ClientForm(),
                "dmd_form":DemandeDecaissementForm(),
                "rapport_form":RapportDepenseForm(),
                "open_change_id": True
            })
                response["HX-Trigger"] ="failed_change_id"
                return response
            
            elif request.user.post.nom == "Employé":
                response = render(request, "employee_templates/creer_rapport.html",{
                "list_demande": list_demande,
                "fond": fond.montant,
                "ch_form": form,  # Le form avec erreurs
                "form": ClientForm(),
                "dmd_form":DemandeDecaissementForm(),
                "rapport_form":RapportDepenseForm(),
                "open_change_id": True
            })
                response["HX-Trigger"] ="failed_change_id"
                return response
                
            
               
    else:
        form = ChangeCredentialsForm(user=request.user)
    return render(request, "directeur_templates/directeur.html", {"ch_form":form,
                                                                  "form": PersonnelRegisterForm()
                                                                  })    


def logout_view(request):
    logout(request)
    return redirect("home_app:home-view")
    