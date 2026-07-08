from django.urls import path

from renewals import views


app_name = 'renewals'

urlpatterns = [
    path('', views.RenewalListView.as_view(), name='renewal_list'),
    path(
        '<int:pk>/',
        views.RenewalDetailView.as_view(),
        name='renewal_detail',
    ),
    path(
        '<int:pk>/editar/',
        views.RenewalUpdateView.as_view(),
        name='renewal_update',
    ),
    path(
        '<int:pk>/renovar/',
        views.RenewPolicyActionView.as_view(),
        name='renewal_renew',
    ),
]
