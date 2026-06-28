from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Client(TenantAwareModel):
    class PersonType(models.TextChoices):
        NATURAL = 'PF', _('Pessoa Física')
        LEGAL = 'PJ', _('Pessoa Jurídica')

    class AISummaryStatus(models.TextChoices):
        IDLE = 'idle', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        DONE = 'done', _('Concluído')
        ERROR = 'error', _('Erro')

    person_type = models.CharField(
        max_length=2,
        choices=PersonType.choices,
        default=PersonType.NATURAL,
    )
    name = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    document = models.CharField(max_length=18)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    address_line = models.CharField(max_length=200, blank=True)
    address_number = models.CharField(max_length=20, blank=True)
    address_complement = models.CharField(max_length=80, blank=True)
    district = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    notes = models.TextField(blank=True)

    ai_summary = models.TextField(blank=True)
    ai_summary_status = models.CharField(
        max_length=12,
        choices=AISummaryStatus.choices,
        default=AISummaryStatus.IDLE,
    )
    ai_summary_updated_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'document'],
                name='client_unique_document_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'name']),
            models.Index(fields=['brokerage', 'is_active']),
        ]

    def __str__(self):
        return self.name
