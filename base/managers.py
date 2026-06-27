from contextvars import ContextVar

from django.db import models


current_tenant = ContextVar('current_tenant', default=None)


class TenantManager(models.Manager):
    def for_tenant(self, tenant):
        return self.filter(brokerage=tenant)
