from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin
from documents.models import Document
from insurance.forms import (
    CoveredItemFormSet,
    ProposalForm,
    ProposalSearchForm,
)
from insurance.models import Proposal


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
        return context
