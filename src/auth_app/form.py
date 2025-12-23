from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.forms import PasswordChangeForm
from .models import Personnel

class PersonnelRegisterForm(forms.ModelForm):
    date_de_naissance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = Personnel
        fields = [
            "first_name",
            "last_name", 
            "email",
            "post",
            "telephone",
            "date_de_naissance",
            "lieu_de_naissance",
            "personne_a_prevenir_en_cas"
        ]
        
class ChangeCredentialsForm(forms.Form):
    new_username = forms.CharField(max_length=150, required=False, label="Nouveau nom d'utilisateur")
    current_password =  forms.CharField(widget=forms.PasswordInput, label="Mot de passe actuel")
    new_password = forms.CharField(widget=forms.PasswordInput, required=False, label="Nouveau mot de asse")  
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label="confirmez nouveau mot de passe")
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get("confirm_password")
        
        #Verification mot de passe actuel
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Mot de passe actuel incorrect")
        
        #verifie si nouveau mots de passe correspondent
        if new_password and new_password != confirm_password:
            raise forms.ValidationError("Les nouveaux mots de passe ne correspondent pas")
        
        return cleaned_data
        