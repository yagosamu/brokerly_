from django.urls import path

from clients import views


app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('novo/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path(
        '<int:pk>/editar/',
        views.ClientUpdateView.as_view(),
        name='client_update',
    ),
]
