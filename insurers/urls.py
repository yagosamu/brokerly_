from django.urls import path

from insurers import views


app_name = 'insurers'

urlpatterns = [
    path('seguradoras/', views.InsurerListView.as_view(), name='insurer_list'),
    path(
        'seguradoras/nova/',
        views.InsurerCreateView.as_view(),
        name='insurer_create',
    ),
    path(
        'seguradoras/<int:pk>/editar/',
        views.InsurerUpdateView.as_view(),
        name='insurer_update',
    ),
    path('ramos/', views.LineOfBusinessListView.as_view(), name='lob_list'),
    path(
        'ramos/novo/',
        views.LineOfBusinessCreateView.as_view(),
        name='lob_create',
    ),
    path(
        'ramos/<int:pk>/editar/',
        views.LineOfBusinessUpdateView.as_view(),
        name='lob_update',
    ),
]
