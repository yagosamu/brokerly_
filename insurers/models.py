from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Insurer(TenantAwareModel):
    name = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18)
    susep_code = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'name'],
                name='insurer_unique_name_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'is_active']),
        ]

    def __str__(self):
        return self.name


class LineOfBusiness(TenantAwareModel):
    class Category(models.TextChoices):
        AUTO = 'auto', _('Automóvel')
        LIFE = 'life', _('Vida')
        PROPERTY = 'property', _('Patrimonial')
        BUSINESS = 'business', _('Empresarial')
        TRAVEL = 'travel', _('Viagem')
        HEALTH = 'health', _('Saúde')
        OTHER = 'other', _('Outros')

    name = models.CharField(max_length=120)
    code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Código SUSEP',
    )
    category = models.CharField(
        max_length=12,
        choices=Category.choices,
        default=Category.OTHER,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'ramo'
        verbose_name_plural = 'ramos'
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'name'],
                name='lob_unique_name_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'is_active']),
            models.Index(fields=['brokerage', 'category']),
        ]

    def __str__(self):
        return self.name
