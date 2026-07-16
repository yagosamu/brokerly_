from django.contrib import admin
from django.urls import include, path

from ai_agents.views import ChatPageView
from dashboard.views import DashboardView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('corretora/', include('tenants.urls')),
    path('anexos/', include('documents.urls')),
    path('clientes/', include('clients.urls')),
    path('sinistros/', include('claims.urls')),
    path('comissoes/', include('commissions.urls')),
    path('crm/', include('crm.urls')),
    path('notifications/', include('notifications.urls')),
    path('renovacoes/', include('renewals.urls')),
    path('ai/', include('ai_agents.urls')),
    path('chat/', ChatPageView.as_view(), name='chat_page'),
    path('relatorios/', include('reports.urls')),
    path('', include('insurers.urls')),
    path('', include('insurance.urls')),
    path('', include('partners.urls')),
    path('', DashboardView.as_view(), name='home'),
]
