from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Claim(TenantAwareModel):
    class Status(models.TextChoices):
        OPENED = 'opened', _('Aberto')
        UNDER_ANALYSIS = 'under_analysis', _('Em análise')
        APPROVED = 'approved', _('Aprovado')
        DENIED = 'denied', _('Negado')
        PAID = 'paid', _('Pago')
        CLOSED = 'closed', _('Encerrado')

    class AISummaryStatus(models.TextChoices):
        IDLE = 'idle', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        DONE = 'done', _('Concluído')
        ERROR = 'error', _('Erro')

    claim_number = models.CharField(max_length=40)
    policy = models.ForeignKey(
        'insurance.Policy',
        on_delete=models.PROTECT,
        related_name='claims',
    )
    covered_item = models.ForeignKey(
        'insurance.CoveredItem',
        on_delete=models.PROTECT,
        related_name='claims',
    )
    occurrence_date = models.DateField()
    notice_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPENED,
    )
    description = models.TextField(blank=True)
    claimed_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    ai_summary = models.TextField(blank=True)
    ai_summary_status = models.CharField(
        max_length=12,
        choices=AISummaryStatus.choices,
        default=AISummaryStatus.IDLE,
    )
    ai_summary_updated_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims_created',
    )

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'claim_number'],
                name='claim_unique_number_per_brokerage',
            ),
            models.CheckConstraint(
                name='claim_occurrence_le_notice',
                condition=models.Q(
                    occurrence_date__lte=models.F('notice_date'),
                ),
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'status']),
            models.Index(fields=['brokerage', '-occurrence_date']),
        ]

    def __str__(self):
        return f'Sinistro {self.claim_number}'
