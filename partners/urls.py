from django.urls import path

from partners import views


app_name = 'partners'

urlpatterns = [
    path('agentes/', views.AgentListView.as_view(), name='agent_list'),
    path('agentes/novo/', views.AgentCreateView.as_view(), name='agent_create'),
    path(
        'agentes/<int:pk>/',
        views.AgentDetailView.as_view(),
        name='agent_detail',
    ),
    path(
        'agentes/<int:pk>/editar/',
        views.AgentUpdateView.as_view(),
        name='agent_update',
    ),
    path(
        'produtores/',
        views.ProducerListView.as_view(),
        name='producer_list',
    ),
    path(
        'produtores/novo/',
        views.ProducerCreateView.as_view(),
        name='producer_create',
    ),
    path(
        'produtores/<int:pk>/',
        views.ProducerDetailView.as_view(),
        name='producer_detail',
    ),
    path(
        'produtores/<int:pk>/editar/',
        views.ProducerUpdateView.as_view(),
        name='producer_update',
    ),
]
