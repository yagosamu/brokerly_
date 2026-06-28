from django.urls import path

from tenants import views


app_name = 'tenants'

urlpatterns = [
    path('onboarding/', views.BrokerageOnboardingView.as_view(), name='onboarding'),
    path('plano/', views.MyPlanView.as_view(), name='my_plan'),
]
