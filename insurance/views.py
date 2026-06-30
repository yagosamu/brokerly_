from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from documents.models import Document
from insurance.forms import (
    CoveredItemFormSet,
    EndorsementForm,
    EndorsementSearchForm,
    PolicyForm,
    PolicySearchForm,
    ProposalForm,
    ProposalSearchForm,
)
from insurance.models import Endorsement, Policy, Proposal
from insurance.services import (
    PolicyGenerationError,
    generate_policy_from_proposal,
)


class ProposalListView(RoleRequiredMixin, ListView):
    template_name = 'insurance/proposal_list.html'
    model = Proposal
    context_object_name = 'proposals'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = Proposal.objects.filter(
            brokerage=self.request.tenant,
        ).select_related('client', 'insurer', 'line_of_business')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(number__icontains=query)
                | Q(client__name__icontains=query)
                | Q(client__document__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        insurer = self.request.GET.get('insurer', '').strip()
        if insurer:
            queryset = queryset.filter(insurer_id=insurer)
        line_of_business = self.request.GET.get(
            'line_of_business',
            '',
        ).strip()
        if line_of_business:
            queryset = queryset.filter(line_of_business_id=line_of_business)
        date_from = self.request.GET.get('date_from', '').strip()
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProposalSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_insurer'] = self.request.GET.get('insurer', '')
        context['selected_lob'] = self.request.GET.get(
            'line_of_business',
            '',
        )
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['statuses'] = Proposal.Status.choices
        context['total'] = self.get_queryset().count()
        return context


class ProposalFormsetMixin:
    def get_formset(self):
        if hasattr(self, 'formset'):
            return self.formset
        instance = getattr(self, 'object', None)
        return CoveredItemFormSet(
            self.request.POST or None,
            instance=instance,
        )

    def save_formset(self, formset):
        for item_form in formset.forms:
            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                item_form.instance.brokerage = self.request.tenant
        formset.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self.get_formset()
        return context


class ProposalCreateView(
    ProposalFormsetMixin,
    RoleRequiredMixin,
    CreateView,
):
    template_name = 'insurance/proposal_form.html'
    form_class = ProposalForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent', 'producer')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        form.instance.created_by = self.request.user
        self.object = form.save()
        self.formset = CoveredItemFormSet(
            self.request.POST,
            instance=self.object,
        )
        if self.formset.is_valid():
            self.save_formset(self.formset)
            return redirect(self.get_success_url())
        transaction.set_rollback(True)
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            'insurance:proposal_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class ProposalUpdateView(
    ProposalFormsetMixin,
    RoleRequiredMixin,
    UpdateView,
):
    template_name = 'insurance/proposal_form.html'
    form_class = ProposalForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_queryset(self):
        return Proposal.objects.filter(brokerage=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()
        self.formset = CoveredItemFormSet(
            self.request.POST,
            instance=self.object,
        )
        if self.formset.is_valid():
            self.save_formset(self.formset)
            return redirect(self.get_success_url())
        transaction.set_rollback(True)
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            'insurance:proposal_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class ProposalDetailView(RoleRequiredMixin, DetailView):
    template_name = 'insurance/proposal_detail.html'
    model = Proposal
    context_object_name = 'proposal'
    allowed_roles = ()

    def get_queryset(self):
        return Proposal.objects.filter(
            brokerage=self.request.tenant,
        ).select_related('client', 'insurer', 'line_of_business', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['covered_items'] = self.object.covered_items.all()
        context['active_tab'] = self.request.GET.get('tab', 'info')
        proposal_content_type = ContentType.objects.get_for_model(Proposal)
        context['attachment_content_type_id'] = proposal_content_type.id
        context['proposal_documents'] = Document.objects.filter(
            brokerage=self.request.tenant,
            content_type=proposal_content_type,
            object_id=self.object.id,
        ).select_related('uploaded_by').order_by('-created_at')
        role = self.request.user.role
        context['can_upload_documents'] = role in (
            'owner',
            'manager',
            'broker',
        )
        context['can_delete_documents'] = role in ('owner', 'manager')
        context['can_generate_policy'] = (
            self.object.status != Proposal.Status.CONVERTED
            and role in ('owner', 'manager', 'broker', 'agent')
        )
        return context


class PolicyListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'insurance/policy_list.html'
    model = Policy
    context_object_name = 'policies'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'client',
            'insurer',
            'line_of_business',
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(policy_number__icontains=query)
                | Q(client__name__icontains=query)
                | Q(client__document__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        insurer = self.request.GET.get('insurer', '').strip()
        if insurer:
            queryset = queryset.filter(insurer_id=insurer)
        line_of_business = self.request.GET.get(
            'line_of_business',
            '',
        ).strip()
        if line_of_business:
            queryset = queryset.filter(line_of_business_id=line_of_business)
        date_from = self.request.GET.get('date_from', '').strip()
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PolicySearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_insurer'] = self.request.GET.get('insurer', '')
        context['selected_lob'] = self.request.GET.get(
            'line_of_business',
            '',
        )
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['statuses'] = Policy.Status.choices
        context['total'] = self.get_queryset().count()
        return context


class PolicyCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'insurance/policy_form.html'
    form_class = PolicyForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'insurance:policy_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class PolicyUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'insurance/policy_form.html'
    form_class = PolicyForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_queryset(self):
        return super().get_queryset()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            'insurance:policy_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class PolicyDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'insurance/policy_detail.html'
    model = Policy
    context_object_name = 'policy'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'proposal',
            'client',
            'insurer',
            'line_of_business',
            'created_by',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['covered_items'] = self.object.covered_items.all()
        context['active_tab'] = self.request.GET.get('tab', 'info')
        policy_content_type = ContentType.objects.get_for_model(Policy)
        context['attachment_content_type_id'] = policy_content_type.id
        context['policy_documents'] = Document.objects.filter(
            brokerage=self.request.tenant,
            content_type=policy_content_type,
            object_id=self.object.id,
        ).select_related('uploaded_by').order_by('-created_at')
        role = self.request.user.role
        context['can_upload_documents'] = role in (
            'owner',
            'manager',
            'broker',
        )
        context['can_delete_documents'] = role in ('owner', 'manager')
        return context


class GeneratePolicyFromProposalView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager', 'broker', 'agent')
    http_method_names = ('post',)

    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal,
            pk=pk,
            brokerage=request.tenant,
        )
        policy_number = request.POST.get('policy_number', '')
        try:
            policy = generate_policy_from_proposal(
                proposal=proposal,
                policy_number=policy_number,
                user=request.user,
            )
        except PolicyGenerationError as error:
            messages.error(request, str(error))
            return redirect('insurance:proposal_detail', pk=proposal.id)
        messages.success(
            request,
            f'Apólice #{policy.policy_number} gerada com sucesso.',
        )
        return redirect('insurance:policy_detail', pk=policy.id)


class EndorsementListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'insurance/endorsement_list.html'
    model = Endorsement
    context_object_name = 'endorsements'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related('policy')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(endorsement_number__icontains=query)
                | Q(policy__policy_number__icontains=query)
                | Q(description__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        endorsement_type = self.request.GET.get('type', '').strip()
        if endorsement_type:
            queryset = queryset.filter(type=endorsement_type)
        policy = self.request.GET.get('policy', '').strip()
        if policy:
            queryset = queryset.filter(policy_id=policy)
        date_from = self.request.GET.get('date_from', '').strip()
        if date_from:
            queryset = queryset.filter(effective_date__gte=date_from)
        date_to = self.request.GET.get('date_to', '').strip()
        if date_to:
            queryset = queryset.filter(effective_date__lte=date_to)
        return queryset.order_by('-effective_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = EndorsementSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_policy'] = self.request.GET.get('policy', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['statuses'] = Endorsement.Status.choices
        context['types'] = Endorsement.Type.choices
        context['total'] = self.get_queryset().count()
        return context


class EndorsementCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'insurance/endorsement_form.html'
    form_class = EndorsementForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'insurance:endorsement_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class EndorsementUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'insurance/endorsement_form.html'
    model = Endorsement
    form_class = EndorsementForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            'insurance:endorsement_detail',
            args=[self.object.id],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class EndorsementDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'insurance/endorsement_detail.html'
    model = Endorsement
    context_object_name = 'endorsement'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy',
            'created_by',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = self.request.GET.get('tab', 'info')
        endorsement_content_type = ContentType.objects.get_for_model(Endorsement)
        context['attachment_content_type_id'] = endorsement_content_type.id
        context['endorsement_documents'] = Document.objects.filter(
            brokerage=self.request.tenant,
            content_type=endorsement_content_type,
            object_id=self.object.id,
        ).select_related('uploaded_by').order_by('-created_at')
        role = self.request.user.role
        context['can_upload_documents'] = role in (
            'owner',
            'manager',
            'broker',
        )
        context['can_delete_documents'] = role in ('owner', 'manager')
        return context
