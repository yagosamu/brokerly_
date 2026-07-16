from django.conf import settings
from django.db import models

from base.models import TenantAwareModel


class ReportJob(TenantAwareModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PROCESSING = 'processing', 'Processando'
        DONE = 'done', 'Concluído'
        ERROR = 'error', 'Erro'

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_jobs',
    )
    report_type = models.CharField(max_length=32)
    params = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['brokerage', 'requested_by', '-created_at']),
            models.Index(fields=['brokerage', 'status']),
        ]

    def __str__(self):
        return f'{self.report_type} · {self.get_status_display()}'
