from django.urls import path

from insurance import views


app_name = 'insurance'

urlpatterns = [
    path(
        'endossos/',
        views.EndorsementListView.as_view(),
        name='endorsement_list',
    ),
    path(
        'endossos/novo/',
        views.EndorsementCreateView.as_view(),
        name='endorsement_create',
    ),
    path(
        'endossos/<int:pk>/',
        views.EndorsementDetailView.as_view(),
        name='endorsement_detail',
    ),
    path(
        'endossos/<int:pk>/editar/',
        views.EndorsementUpdateView.as_view(),
        name='endorsement_update',
    ),
    path('apolices/', views.PolicyListView.as_view(), name='policy_list'),
    path(
        'apolices/nova/',
        views.PolicyCreateView.as_view(),
        name='policy_create',
    ),
    path(
        'apolices/<int:pk>/',
        views.PolicyDetailView.as_view(),
        name='policy_detail',
    ),
    path(
        'apolices/<int:pk>/editar/',
        views.PolicyUpdateView.as_view(),
        name='policy_update',
    ),
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
    path(
        'propostas/<int:pk>/gerar-apolice/',
        views.GeneratePolicyFromProposalView.as_view(),
        name='proposal_generate_policy',
    ),
]
