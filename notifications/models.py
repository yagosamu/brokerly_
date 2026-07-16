from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Notification(TenantAwareModel):
    class Type(models.TextChoices):
        AI_SUMMARY = 'ai_summary', _('Resumo de IA')
        REPORT = 'report', _('Relatório')
        REPORT_READY = 'report_ready', _('Relatório pronto')
        RENEWAL = 'renewal', _('Renovação')
        SYSTEM = 'system', _('Sistema')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_type_display()} · {self.title}'

    def clean(self):
        super().clean()
        if (
            self.user_id
            and self.brokerage_id
            and self.user.brokerage_id != self.brokerage_id
        ):
            raise ValidationError({'user': 'Usuário inválido.'})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
