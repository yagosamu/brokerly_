from django.conf import settings
from django.db import models

from base.models import BaseModel


class Plan(BaseModel):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=40, unique=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    max_users = models.PositiveIntegerField(null=True, blank=True)
    max_clients = models.PositiveIntegerField(null=True, blank=True)
    max_policies = models.PositiveIntegerField(null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    is_available = models.BooleanField(default=False)

    class Meta:
        ordering = ('price',)

    def __str__(self):
        return self.name


class Brokerage(BaseModel):
    legal_name = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField(max_length=18, unique=True)
    susep_code = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line = models.CharField(max_length=200, blank=True)
    address_number = models.CharField(max_length=20, blank=True)
    address_complement = models.CharField(max_length=80, blank=True)
    district = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_brokerages',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='brokerages',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('legal_name',)

    def __str__(self):
        return self.legal_name
