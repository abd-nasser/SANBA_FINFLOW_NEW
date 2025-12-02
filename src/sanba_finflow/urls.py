from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("auth_app.urls")),
    path("directeur/", include("directeur_app.urls")),
    path("secretaire", include("secretaire_app.urls")),
    path("employee/", include("employee_app.urls")),
    path("comptable/", include("comptable_app.urls")),
    path("client/", include("client_app.urls")),
    path("chantier/", include("chantier_app.urls")),
    path("dashboard/", include("dashboard_app.urls"))
    
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)