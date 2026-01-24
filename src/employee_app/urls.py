from django.urls import path
from . import views

app_name = "employee_app"

urlpatterns = [
    path("interface-employee", views.CreerRapportDepenseView.as_view(), name="employee-view" ),
    path('Mes-rapports', views.MesRapportsView.as_view(), name='mes-rapports'),
    path('employee/du/mois', views.BestEmployeeView.as_view(), name='employee-du-mois'),
    path("modifier/<int:pk>/rapport",views.UpdateRapportView.as_view(), name='modifier-rapport'),
]
