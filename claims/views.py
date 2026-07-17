from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from claims.forms import ClaimForm, ClaimSearchForm
from claims.models import Claim
from documents.models import Document


class ClaimListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'claims/claim_list.html'
    model = Claim
    context_object_name = 'claims'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'policy',
            'policy__client',
            'policy__insurer',
            'covered_item',
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(claim_number__icontains=query)
                | Q(policy__policy_number__icontains=query)
                | Q(covered_item__description__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        policy = self.request.GET.get('policy', '').strip()
        if policy:
            queryset = queryset.filter(policy_id=policy)
        date_from = self.request.GET.get('date_from', '').strip()
        if date_from:
            queryset = queryset.filter(occurrence_date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(occurrence_date__lte=date_to)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClaimSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_policy'] = self.request.GET.get('policy', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['statuses'] = Claim.Status.choices
        context['total'] = self.get_queryset().count()
        return context


class ClaimCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'claims/claim_form.html'
    form_class = ClaimForm
    allowed_roles = (
        'owner',
        'manager',
        'broker',
        'agent',
        'producer',
        'operational',
    )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('claims:claim_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class ClaimUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'claims/claim_form.html'
    model = Claim
    form_class = ClaimForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy('claims:claim_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class ClaimDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'claims/claim_detail.html'
    model = Claim
    context_object_name = 'claim'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy',
            'covered_item',
            'created_by',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = self.request.GET.get('tab', 'info')
        claim_content_type = ContentType.objects.get_for_model(Claim)
        context['attachment_content_type_id'] = claim_content_type.id
        context['claim_documents'] = Document.objects.filter(
            brokerage=self.request.tenant,
            content_type=claim_content_type,
            object_id=self.object.id,
        ).select_related('uploaded_by').order_by('-created_at')
        role = self.request.user.role
        context['can_upload_documents'] = role in (
            'owner',
            'manager',
            'broker',
            'operational',
        )
        context['can_delete_documents'] = role in ('owner', 'manager')
        return context
