from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Personnel

class PersonnelRegisterForm(UserCreationForm):
    date_de_naissance = forms.DateField(widget=forms.DateInput(attrs={
        'placeholder':'jj/mm/an'
    }))
                
    class Meta:
        model = Personnel
        fields = [
                  "username",
                  "first_name",
                  "last_name", 
                  "email",
                  "post",
                  "telephone",
                  "date_de_naissance",
                  "lieu_de_naissance",
                  "personne_a_prevenir_en_cas"]
       