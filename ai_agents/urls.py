from django.urls import path

from . import views


app_name = 'ai_agents'

urlpatterns = [
    path('chat/', views.ChatSessionListCreateView.as_view(), name='chat_sessions'),
    path(
        'chat/<int:session_id>/messages/',
        views.ChatSessionMessagesView.as_view(),
        name='chat_messages',
    ),
    path(
        'chat/<int:session_id>/rename/',
        views.ChatSessionRenameView.as_view(),
        name='chat_rename',
    ),
    path(
        'chat/<int:session_id>/delete/',
        views.ChatSessionDeleteView.as_view(),
        name='chat_delete',
    ),
    path(
        'chat/<int:session_id>/stream/',
        views.ChatMessageStreamView.as_view(),
        name='chat_stream',
    ),
    path('summarize/<str:entity_type>/<int:pk>/', views.trigger_summary, name='summarize'),
    path(
        'summary-status/<str:entity_type>/<int:pk>/',
        views.summary_status,
        name='summary_status',
    ),
]
