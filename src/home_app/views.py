from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm

def home_view(request):
    ctx ={"form":AuthenticationForm()}
    return render(request, "home.html", ctx)
