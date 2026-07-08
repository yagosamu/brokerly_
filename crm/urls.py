from django.urls import path

from crm import views


app_name = 'crm'

urlpatterns = [
    path('kanban/', views.KanbanView.as_view(), name='kanban'),
    path('negociacoes/', views.DealListView.as_view(), name='deal_list'),
    path('negociacoes/nova/', views.DealCreateView.as_view(), name='deal_create'),
    path(
        'negociacoes/<int:pk>/',
        views.DealDetailView.as_view(),
        name='deal_detail',
    ),
    path(
        'negociacoes/<int:pk>/editar/',
        views.DealUpdateView.as_view(),
        name='deal_update',
    ),
    path(
        'negociacoes/<int:pk>/mover/',
        views.DealMoveStageView.as_view(),
        name='deal_move_stage',
    ),
    path('pipelines/', views.PipelineListView.as_view(), name='pipeline_list'),
    path(
        'pipelines/novo/',
        views.PipelineCreateView.as_view(),
        name='pipeline_create',
    ),
    path(
        'pipelines/<int:pk>/editar/',
        views.PipelineUpdateView.as_view(),
        name='pipeline_update',
    ),
]
