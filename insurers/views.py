from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from base.mixins import RoleRequiredMixin
from insurers.forms import (
    InsurerForm,
    InsurerSearchForm,
    LineOfBusinessForm,
    LineOfBusinessSearchForm,
)
from insurers.models import Insurer, LineOfBusiness


class InsurerListView(RoleRequiredMixin, ListView):
    template_name = 'insurers/insurer_list.html'
    model = Insurer
    context_object_name = 'insurers'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = Insurer.objects.filter(
            brokerage=self.request.tenant,
        ).order_by('name')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(cnpj__icontains=query)
                | Q(susep_code__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = InsurerSearchForm(self.request.GET or None)
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['total'] = self.get_queryset().count()
        return context


class InsurerCreateView(RoleRequiredMixin, CreateView):
    template_name = 'insurers/insurer_form.html'
    form_class = InsurerForm
    success_url = reverse_lazy('insurers:insurer_list')
    allowed_roles = ('owner', 'manager', 'broker')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        return super().form_valid(form)


class InsurerUpdateView(RoleRequiredMixin, UpdateView):
    template_name = 'insurers/insurer_form.html'
    form_class = InsurerForm
    success_url = reverse_lazy('insurers:insurer_list')
    allowed_roles = ('owner', 'manager', 'broker')

    def get_queryset(self):
        return Insurer.objects.filter(brokerage=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs


class LineOfBusinessListView(RoleRequiredMixin, ListView):
    template_name = 'insurers/lineofbusiness_list.html'
    model = LineOfBusiness
    context_object_name = 'lines_of_business'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = LineOfBusiness.objects.filter(
            brokerage=self.request.tenant,
        ).order_by('name')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        category = self.request.GET.get('category', '').strip()
        if category:
            queryset = queryset.filter(category=category)
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LineOfBusinessSearchForm(
            self.request.GET or None
        )
        context['q'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['categories'] = LineOfBusiness.Category.choices
        context['total'] = self.get_queryset().count()
        return context


class LineOfBusinessCreateView(RoleRequiredMixin, CreateView):
    template_name = 'insurers/lineofbusiness_form.html'
    form_class = LineOfBusinessForm
    success_url = reverse_lazy('insurers:lob_list')
    allowed_roles = ('owner', 'manager', 'broker')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        return super().form_valid(form)


class LineOfBusinessUpdateView(RoleRequiredMixin, UpdateView):
    template_name = 'insurers/lineofbusiness_form.html'
    form_class = LineOfBusinessForm
    success_url = reverse_lazy('insurers:lob_list')
    allowed_roles = ('owner', 'manager', 'broker')

    def get_queryset(self):
        return LineOfBusiness.objects.filter(brokerage=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs
