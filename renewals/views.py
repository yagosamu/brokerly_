from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from renewals.forms import RenewalForm, RenewalSearchForm, RenewPolicyForm
from renewals.models import Renewal
from renewals.services import RenewalError, renew_policy


class RenewalListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'renewals/renewal_list.html'
    model = Renewal
    context_object_name = 'renewals'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'policy',
            'policy__client',
            'new_policy',
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(policy__policy_number__icontains=query)
                | Q(policy__client__name__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        date_from = self.request.GET.get('date_from', '').strip()
        if date_from:
            queryset = queryset.filter(due_date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(due_date__lte=date_to)
        return queryset.order_by('due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RenewalSearchForm(self.request.GET or None)
        context.update(
            self.get_queryset().aggregate(
                total_pending_count=Count(
                    'id',
                    filter=Q(status=Renewal.Status.PENDING),
                ),
                total_in_progress_count=Count(
                    'id',
                    filter=Q(status=Renewal.Status.IN_PROGRESS),
                ),
                total_renewed_count=Count(
                    'id',
                    filter=Q(status=Renewal.Status.RENEWED),
                ),
                total_lost_count=Count(
                    'id',
                    filter=Q(status=Renewal.Status.LOST),
                ),
                total_not_renewed_count=Count(
                    'id',
                    filter=Q(status=Renewal.Status.NOT_RENEWED),
                ),
            )
        )
        return context


class RenewalDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'renewals/renewal_detail.html'
    model = Renewal
    context_object_name = 'renewal'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy',
            'policy__client',
            'policy__insurer',
            'policy__line_of_business',
            'new_policy',
            'created_by',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['renew_form'] = RenewPolicyForm()
        return context


class RenewalUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'renewals/renewal_form.html'
    model = Renewal
    form_class = RenewalForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy',
            'policy__client',
        )

    def get_success_url(self):
        return reverse_lazy('renewals:renewal_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class RenewPolicyActionView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager', 'broker')
    http_method_names = ('post',)

    def post(self, request, pk):
        renewal = get_object_or_404(
            Renewal.objects.select_related('policy'),
            pk=pk,
            brokerage=request.tenant,
        )
        form = RenewPolicyForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Informe o número da nova apólice.')
            return redirect('renewals:renewal_detail', pk=renewal.id)
        try:
            new_policy = renew_policy(
                renewal=renewal,
                new_policy_number=form.cleaned_data['new_policy_number'],
                user=request.user,
            )
        except RenewalError as error:
            messages.error(request, str(error))
            return redirect('renewals:renewal_detail', pk=renewal.id)
        messages.success(
            request,
            f'Apólice #{new_policy.policy_number} criada com sucesso.',
        )
        return redirect('insurance:policy_detail', pk=new_policy.id)
