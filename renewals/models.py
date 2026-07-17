from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Renewal(TenantAwareModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        IN_PROGRESS = 'in_progress', _('Em andamento')
        RENEWED = 'renewed', _('Renovada')
        LOST = 'lost', _('Perdida')
        NOT_RENEWED = 'not_renewed', _('Não renovada')

    policy = models.ForeignKey(
        'insurance.Policy',
        on_delete=models.PROTECT,
        related_name='renewals',
    )
    new_policy = models.ForeignKey(
        'insurance.Policy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewal_source',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    due_date = models.DateField(
        help_text='Vencimento da apólice original.',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewals_created',
    )

    class Meta:
        ordering = ('due_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'policy'],
                name='renewal_unique_per_policy',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', '-created_at']),
            models.Index(fields=['brokerage', 'status', 'due_date']),
        ]

    def __str__(self):
        return f'Renovação · #{self.policy.policy_number}'

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.policy_id
            and self.brokerage_id
            and self.policy.brokerage_id != self.brokerage_id
        ):
            errors['policy'] = 'Apólice inválida.'
        if (
            self.new_policy_id
            and self.brokerage_id
            and self.new_policy.brokerage_id != self.brokerage_id
        ):
            errors['new_policy'] = 'Nova apólice inválida.'
        if (
            self.created_by_id
            and self.brokerage_id
            and self.created_by.brokerage_id != self.brokerage_id
        ):
            errors['created_by'] = 'Usuário inválido.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
