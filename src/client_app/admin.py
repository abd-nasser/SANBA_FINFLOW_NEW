from django.contrib import admin
from .models import Client

@admin.register(Client)
class AdminClient(admin.ModelAdmin):
    list_display = ["type_client","nom","prenom","telephone", "email" ]
