from django.urls import path
from . import views

app_name = "employee_app"

urlpatterns = [
    path("interface-employee", views.rapport_depense_view, name="employee-view" )
]
