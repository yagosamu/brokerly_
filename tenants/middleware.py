from base.managers import current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            tenant = getattr(user, 'brokerage', None)

        request.tenant = tenant
        token = current_tenant.set(tenant)
        try:
            return self.get_response(request)
        finally:
            current_tenant.reset(token)
