from django.contrib import admin
from .models import Post, Personnel

@admin.register(Post)
class AdminPost(admin.ModelAdmin):
    list_display = ["nom", "date_creation"]
    

@admin.register(Personnel)
class AdminPersonnel(admin.ModelAdmin):
    list_display = ["post","username", "first_name", "last_name", "telephone", "email", ]

    
    