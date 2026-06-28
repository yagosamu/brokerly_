from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from base.mixins import RoleRequiredMixin
from clients.forms import ClientForm, ClientSearchForm
from clients.models import Client
from documents.models import Document


class ClientListView(RoleRequiredMixin, ListView):
    template_name = 'clients/client_list.html'
    model = Client
    context_object_name = 'clients'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = Client.objects.filter(
            brokerage=self.request.tenant,
        ).order_by('name')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(trade_name__icontains=query)
                | Q(document__icontains=query)
                | Q(email__icontains=query)
            )
        person_type = self.request.GET.get('person_type', '').strip()
        if person_type:
            queryset = queryset.filter(person_type=person_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClientSearchForm(self.request.GET or None)
        context['q'] = self.request.GET.get('q', '')
        context['selected_person_type'] = self.request.GET.get(
            'person_type',
            '',
        )
        context['person_types'] = Client.PersonType.choices
        context['total'] = self.get_queryset().count()
        return context


class ClientCreateView(RoleRequiredMixin, CreateView):
    template_name = 'clients/client_form.html'
    form_class = ClientForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent', 'producer')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('clients:client_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class ClientUpdateView(RoleRequiredMixin, UpdateView):
    template_name = 'clients/client_form.html'
    form_class = ClientForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_queryset(self):
        return Client.objects.filter(brokerage=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy('clients:client_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class ClientDetailView(RoleRequiredMixin, DetailView):
    template_name = 'clients/client_detail.html'
    model = Client
    context_object_name = 'client'
    allowed_roles = ()

    def get_queryset(self):
        return Client.objects.filter(brokerage=self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = self.request.GET.get('tab', 'info')
        client_content_type = ContentType.objects.get_for_model(Client)
        context['attachment_content_type_id'] = client_content_type.id
        context['client_documents'] = Document.objects.filter(
            brokerage=self.request.tenant,
            content_type=client_content_type,
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
