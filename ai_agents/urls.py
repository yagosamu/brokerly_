from django.urls import path

from . import views


app_name = 'ai_agents'

urlpatterns = [
    path('summarize/<str:entity_type>/<int:pk>/', views.trigger_summary, name='summarize'),
    path(
        'summary-status/<str:entity_type>/<int:pk>/',
        views.summary_status,
        name='summary_status',
    ),
]
