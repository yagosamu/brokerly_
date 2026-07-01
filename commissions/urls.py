from django.urls import path

from commissions import views


app_name = 'commissions'

urlpatterns = [
    path('', views.CommissionListView.as_view(), name='commission_list'),
    path(
        '<int:pk>/',
        views.CommissionDetailView.as_view(),
        name='commission_detail',
    ),
    path(
        '<int:pk>/status/',
        views.CommissionStatusUpdateView.as_view(),
        name='commission_status',
    ),
    path(
        '<int:commission_id>/splits/novo/',
        views.CommissionSplitCreateView.as_view(),
        name='split_create',
    ),
    path(
        'splits/<int:pk>/excluir/',
        views.CommissionSplitDeleteView.as_view(),
        name='split_delete',
    ),
]
