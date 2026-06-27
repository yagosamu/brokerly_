from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from accounts.forms import EmailAuthenticationForm, ProfileForm, RegisterForm


class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('accounts:profile')

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
