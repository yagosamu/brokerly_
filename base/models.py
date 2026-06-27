from django.db import models

from base.managers import TenantManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantAwareModel(BaseModel):
    brokerage = models.ForeignKey(
        'tenants.Brokerage',
        on_delete=models.PROTECT,
        related_name='+',
    )

    objects = TenantManager()

    class Meta:
        abstract = True
