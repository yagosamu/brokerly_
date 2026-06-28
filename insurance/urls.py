from django.urls import path

from insurance import views


app_name = 'insurance'

urlpatterns = [
    path('propostas/', views.ProposalListView.as_view(), name='proposal_list'),
    path(
        'propostas/nova/',
        views.ProposalCreateView.as_view(),
        name='proposal_create',
    ),
    path(
        'propostas/<int:pk>/',
        views.ProposalDetailView.as_view(),
        name='proposal_detail',
    ),
    path(
        'propostas/<int:pk>/editar/',
        views.ProposalUpdateView.as_view(),
        name='proposal_update',
    ),
]
