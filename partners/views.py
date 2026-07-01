from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from partners.forms import (
    AgentForm,
    AgentSearchForm,
    ProducerForm,
    ProducerSearchForm,
)
from partners.models import Agent, EntityType, Producer


class AgentListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'partners/agent_list.html'
    model = Agent
    context_object_name = 'agents'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(document__icontains=query)
                | Q(email__icontains=query)
                | Q(susep_code__icontains=query)
            )
        entity_type = self.request.GET.get('entity_type', '').strip()
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AgentSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_entity_type'] = self.request.GET.get(
            'entity_type',
            '',
        )
        context['selected_status'] = self.request.GET.get('status', '')
        context['total'] = self.get_queryset().count()
        context['entity_types'] = EntityType.choices
        return context


class AgentCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'partners/agent_form.html'
    form_class = AgentForm
    allowed_roles = ('owner', 'manager')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('partners:agent_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class AgentUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'partners/agent_form.html'
    model = Agent
    form_class = AgentForm
    allowed_roles = ('owner', 'manager')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy('partners:agent_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class AgentDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'partners/agent_detail.html'
    model = Agent
    context_object_name = 'agent'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related('user')


class ProducerListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'partners/producer_list.html'
    model = Producer
    context_object_name = 'producers'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related('agent', 'user')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(document__icontains=query)
                | Q(email__icontains=query)
                | Q(agent__name__icontains=query)
            )
        entity_type = self.request.GET.get('entity_type', '').strip()
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        agent = self.request.GET.get('agent', '').strip()
        if agent:
            queryset = queryset.filter(agent_id=agent)
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProducerSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_entity_type'] = self.request.GET.get(
            'entity_type',
            '',
        )
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_agent'] = self.request.GET.get('agent', '')
        context['total'] = self.get_queryset().count()
        context['entity_types'] = EntityType.choices
        return context


class ProducerCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'partners/producer_form.html'
    form_class = ProducerForm
    allowed_roles = ('owner', 'manager')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('partners:producer_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class ProducerUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'partners/producer_form.html'
    model = Producer
    form_class = ProducerForm
    allowed_roles = ('owner', 'manager')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy('partners:producer_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class ProducerDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'partners/producer_detail.html'
    model = Producer
    context_object_name = 'producer'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related('agent', 'user')
