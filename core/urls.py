from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('corretora/', include('tenants.urls')),
    path('anexos/', include('documents.urls')),
    path('clientes/', include('clients.urls')),
    path('sinistros/', include('claims.urls')),
    path('comissoes/', include('commissions.urls')),
    path('crm/', include('crm.urls')),
    path('', include('insurers.urls')),
    path('', include('insurance.urls')),
    path('', include('partners.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
