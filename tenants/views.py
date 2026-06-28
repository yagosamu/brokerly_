from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from tenants.forms import BrokerageOnboardingForm
from tenants.models import Plan, Subscription


class BrokerageOnboardingView(LoginRequiredMixin, CreateView):
    template_name = 'tenants/onboarding.html'
    form_class = BrokerageOnboardingForm
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.brokerage_id:
            return redirect('tenants:my_plan')
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        plan = Plan.objects.get(slug='free')
        brokerage = form.save(commit=False)
        brokerage.owner = self.request.user
        brokerage.plan = plan
        brokerage.save()
        self.object = brokerage

        Subscription.objects.create(
            brokerage=brokerage,
            plan=plan,
            status='active',
        )

        self.request.user.brokerage = brokerage
        self.request.user.save(update_fields=['brokerage'])

        messages.success(
            self.request,
            'Corretora criada com sucesso. Bem-vindo ao Brokerly.',
            fail_silently=True,
        )
        return redirect(self.get_success_url())


class MyPlanView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/my_plan.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.all().order_by('price')
        context['brokerage'] = getattr(self.request.user, 'brokerage', None)
        brokerage = context['brokerage']
        context['subscription'] = (
            getattr(brokerage, 'subscription', None) if brokerage else None
        )
        return context
