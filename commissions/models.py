from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Commission(TenantAwareModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        RECEIVED = 'received', _('Recebida')
        PAID = 'paid', _('Repassada')

    policy = models.OneToOneField(
        'insurance.Policy',
        on_delete=models.PROTECT,
        related_name='commission',
    )
    base_premium = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
    )
    insurer_rate = models.DecimalField(
        max_digits=6, decimal_places=4, default=0,
    )
    insurer_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reference_date = models.DateField()
    received_at = models.DateField(null=True, blank=True)
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('-reference_date',)
        indexes = [
            models.Index(fields=['brokerage', 'status']),
            models.Index(fields=['brokerage', '-created_at']),
            models.Index(fields=['brokerage', '-reference_date']),
        ]

    def __str__(self):
        return f'Comissão da apólice #{self.policy.policy_number}'

    def clean(self):
        super().clean()
        if (
            self.policy_id
            and self.brokerage_id
            and self.policy.brokerage_id != self.brokerage_id
        ):
            raise ValidationError({'policy': 'Apólice inválida.'})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def total_split_amount(self):
        if not self.pk:
            return Decimal('0')
        return sum(
            (split.amount for split in self.splits.all()),
            start=Decimal('0'),
        )

    @property
    def remaining_amount(self):
        return self.insurer_amount - self.total_split_amount


class CommissionSplit(TenantAwareModel):
    class BeneficiaryType(models.TextChoices):
        AGENT = 'agent', _('Agente')
        PRODUCER = 'producer', _('Produtor')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PAID = 'paid', _('Pago')

    commission = models.ForeignKey(
        Commission,
        on_delete=models.CASCADE,
        related_name='splits',
    )
    beneficiary_type = models.CharField(
        max_length=10,
        choices=BeneficiaryType.choices,
    )
    agent = models.ForeignKey(
        'partners.Agent',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='commission_splits',
    )
    producer = models.ForeignKey(
        'partners.Producer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='commission_splits',
    )
    rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text='Percentual do prêmio direcionado ao beneficiário.',
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('id',)
        constraints = [
            models.CheckConstraint(
                name='split_exactly_one_beneficiary',
                condition=(
                    models.Q(
                        beneficiary_type='agent',
                        agent__isnull=False,
                        producer__isnull=True,
                    )
                    | models.Q(
                        beneficiary_type='producer',
                        producer__isnull=False,
                        agent__isnull=True,
                    )
                ),
            ),
        ]

    def __str__(self):
        return f'Repasse {self.get_beneficiary_type_display()}'

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.commission_id
            and self.brokerage_id
            and self.commission.brokerage_id != self.brokerage_id
        ):
            errors['commission'] = 'Comissão inválida.'
        if (
            self.agent_id
            and self.brokerage_id
            and self.agent.brokerage_id != self.brokerage_id
        ):
            errors['agent'] = 'Agente inválido.'
        if (
            self.producer_id
            and self.brokerage_id
            and self.producer.brokerage_id != self.brokerage_id
        ):
            errors['producer'] = 'Produtor inválido.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def beneficiary(self):
        if self.beneficiary_type == self.BeneficiaryType.AGENT:
            return self.agent
        return self.producer
