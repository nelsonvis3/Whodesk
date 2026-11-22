from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.tickets.urls")),
    path("api/", include("apps.knowledge.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    # El frontend (SPA con rutas por hash) lo sirve el mismo Django: un solo servicio, un solo hosting.
    path("", ensure_csrf_cookie(TemplateView.as_view(template_name="index.html")), name="app"),
]
