from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from commissions.forms import (
    CommissionSearchForm,
    CommissionSplitForm,
    CommissionStatusForm,
)
from commissions.models import Commission, CommissionSplit


class CommissionListView(
    RoleRequiredMixin,
    TenantQuerysetMixin,
    ListView,
):
    template_name = 'commissions/commission_list.html'
    model = Commission
    context_object_name = 'commissions'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'policy',
            'policy__client',
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
            queryset = queryset.filter(reference_date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(reference_date__lte=date_to)
        return queryset.order_by('-reference_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = CommissionSearchForm(
            self.request.GET or None,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        totals = self.get_queryset().aggregate(
            total_pending_amount=Sum(
                'insurer_amount',
                filter=Q(status=Commission.Status.PENDING),
                default=Decimal('0'),
            ),
            total_pending_count=Count(
                'id',
                filter=Q(status=Commission.Status.PENDING),
            ),
            total_received_amount=Sum(
                'insurer_amount',
                filter=Q(status=Commission.Status.RECEIVED),
                default=Decimal('0'),
            ),
            total_received_count=Count(
                'id',
                filter=Q(status=Commission.Status.RECEIVED),
            ),
            total_paid_amount=Sum(
                'insurer_amount',
                filter=Q(status=Commission.Status.PAID),
                default=Decimal('0'),
            ),
            total_paid_count=Count(
                'id',
                filter=Q(status=Commission.Status.PAID),
            ),
        )
        context.update(totals)
        return context


class CommissionDetailView(
    RoleRequiredMixin,
    TenantQuerysetMixin,
    DetailView,
):
    template_name = 'commissions/commission_detail.html'
    model = Commission
    context_object_name = 'commission'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy',
            'policy__client',
            'policy__insurer',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['splits'] = self.object.splits.select_related(
            'agent',
            'producer',
        )
        context.setdefault(
            'split_form',
            CommissionSplitForm(
                brokerage=self.request.tenant,
                commission=self.object,
            ),
        )
        context['status_form'] = CommissionStatusForm(instance=self.object)
        context['total_split_amount'] = self.object.total_split_amount
        context['remaining_amount'] = self.object.remaining_amount
        return context


class CommissionSplitCreateView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager')

    def post(self, request, commission_id):
        commission = get_object_or_404(
            Commission,
            pk=commission_id,
            brokerage=request.tenant,
        )
        form = CommissionSplitForm(
            request.POST,
            brokerage=request.tenant,
            commission=commission,
        )
        if form.is_valid():
            split = form.save(commit=False)
            split.brokerage = request.tenant
            split.commission = commission
            split.save()
            return redirect('commissions:commission_detail', pk=commission.pk)
        context = {
            'commission': commission,
            'splits': commission.splits.select_related('agent', 'producer'),
            'split_form': form,
            'status_form': CommissionStatusForm(instance=commission),
            'total_split_amount': commission.total_split_amount,
            'remaining_amount': commission.remaining_amount,
        }
        return render(
            request,
            'commissions/commission_detail.html',
            context,
        )


class CommissionSplitDeleteView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager')

    def post(self, request, pk):
        split = get_object_or_404(
            CommissionSplit.objects.select_related('commission'),
            pk=pk,
            brokerage=request.tenant,
            commission__brokerage=request.tenant,
        )
        commission_id = split.commission_id
        split.delete()
        return redirect(
            'commissions:commission_detail',
            pk=commission_id,
        )


class CommissionStatusUpdateView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager')

    def post(self, request, pk):
        commission = get_object_or_404(
            Commission,
            pk=pk,
            brokerage=request.tenant,
        )
        form = CommissionStatusForm(request.POST, instance=commission)
        if form.is_valid():
            form.save()
        return redirect('commissions:commission_detail', pk=commission.pk)
