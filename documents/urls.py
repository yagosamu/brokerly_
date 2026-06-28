from django.urls import path

from documents import views


app_name = 'documents'

urlpatterns = [
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
    path(
        '<int:pk>/baixar/',
        views.ProtectedDocumentDownloadView.as_view(),
        name='download',
    ),
    path('<int:pk>/excluir/', views.DocumentDeleteView.as_view(), name='delete'),
]
