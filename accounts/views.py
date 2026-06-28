from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.forms import (
    EmailAuthenticationForm,
    MemberCreateForm,
    MemberUpdateForm,
    ProfileForm,
    RegisterForm,
)
from accounts.models import User
from base.mixins import RoleRequiredMixin


class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('tenants:onboarding')

    def form_valid(self, form):
        self.object = form.save()
        login(
            self.request,
            self.object,
            backend='accounts.backends.EmailBackend',
        )
        return redirect(self.success_url)


class EmailLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user


class MemberListView(RoleRequiredMixin, ListView):
    template_name = 'accounts/member_list.html'
    model = User
    context_object_name = 'members'
    paginate_by = 25
    allowed_roles = (User.Role.OWNER, User.Role.MANAGER)

    def get_queryset(self):
        queryset = User.objects.filter(
            brokerage=self.request.tenant,
        ).order_by('first_name', 'email')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        role = self.request.GET.get('role', '').strip()
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['selected_role'] = self.request.GET.get('role', '')
        context['roles'] = User.Role.choices
        context['plan'] = self.request.tenant.plan
        context['active_count'] = User.objects.filter(
            brokerage=self.request.tenant,
            is_active=True,
        ).count()
        return context


class MemberCreateView(RoleRequiredMixin, CreateView):
    template_name = 'accounts/member_form.html'
    form_class = MemberCreateForm
    success_url = reverse_lazy('accounts:member_list')
    allowed_roles = (User.Role.OWNER, User.Role.MANAGER)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class MemberUpdateView(RoleRequiredMixin, UpdateView):
    template_name = 'accounts/member_form.html'
    form_class = MemberUpdateForm
    success_url = reverse_lazy('accounts:member_list')
    allowed_roles = (User.Role.OWNER, User.Role.MANAGER)

    def get_queryset(self):
        return User.objects.filter(brokerage=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['requesting_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context
