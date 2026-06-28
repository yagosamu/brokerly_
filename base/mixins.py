from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden


class TenantQuerysetMixin:
    """Filter a queryset by the tenant resolved for the current request."""

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = getattr(self.request, 'tenant', None)
        if tenant is None:
            return queryset.none()
        return queryset.filter(brokerage=tenant)


class RoleRequiredMixin(LoginRequiredMixin):
    """Require an authenticated user linked to a brokerage."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.brokerage is None:
            return HttpResponseForbidden('Conta sem corretora vinculada.')
        # Role validation is enabled in Sprint 7.
        return super().dispatch(request, *args, **kwargs)
