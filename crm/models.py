from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Pipeline(TenantAwareModel):
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'name'],
                name='pipeline_unique_name_per_brokerage',
            ),
        ]

    def __str__(self):
        return self.name


class Stage(TenantAwareModel):
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name='stages',
    )
    name = models.CharField(max_length=80)
    color = models.CharField(
        max_length=7,
        default='#3454d1',
        help_text='Hex color, ex.: #3454d1',
    )
    order = models.PositiveIntegerField(default=0)
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ('pipeline', 'order', 'id')
        constraints = [
            models.CheckConstraint(
                name='stage_won_xor_lost',
                condition=~(
                    models.Q(is_won=True)
                    & models.Q(is_lost=True)
                ),
            ),
        ]

    def __str__(self):
        return f'{self.pipeline.name} · {self.name}'

    def clean(self):
        super().clean()
        if (
            self.pipeline_id
            and self.brokerage_id
            and self.pipeline.brokerage_id != self.brokerage_id
        ):
            raise ValidationError({'pipeline': 'Pipeline inválido.'})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class Deal(TenantAwareModel):
    class Status(models.TextChoices):
        OPEN = 'open', _('Aberta')
        WON = 'won', _('Ganha')
        LOST = 'lost', _('Perdida')

    class AISummaryStatus(models.TextChoices):
        IDLE = 'idle', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        DONE = 'done', _('Concluído')
        ERROR = 'error', _('Erro')

    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.PROTECT,
        related_name='deals',
    )
    stage = models.ForeignKey(
        Stage,
        on_delete=models.PROTECT,
        related_name='deals',
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='deals',
    )
    producer = models.ForeignKey(
        'partners.Producer',
        on_delete=models.PROTECT,
        related_name='deals',
    )
    agent = models.ForeignKey(
        'partners.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
    )
    line_of_business = models.ForeignKey(
        'insurers.LineOfBusiness',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
    )
    proposal = models.ForeignKey(
        'insurance.Proposal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    estimated_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        max_length=6,
        choices=Status.choices,
        default=Status.OPEN,
    )
    expected_close_date = models.DateField(null=True, blank=True)
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
        related_name='deals_created',
    )

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['brokerage', 'status']),
            models.Index(fields=['brokerage', 'stage']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        self._validate_fk_brokerage(
            errors,
            'pipeline',
            self.pipeline if self.pipeline_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'stage',
            self.stage if self.stage_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'client',
            self.client if self.client_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'producer',
            self.producer if self.producer_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'agent',
            self.agent if self.agent_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'line_of_business',
            self.line_of_business if self.line_of_business_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'insurer',
            self.insurer if self.insurer_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'proposal',
            self.proposal if self.proposal_id else None,
        )
        if (
            self.created_by_id
            and self.brokerage_id
            and self.created_by.brokerage_id != self.brokerage_id
        ):
            errors['created_by'] = 'Usuário inválido.'
        if (
            self.stage_id
            and self.pipeline_id
            and self.stage.pipeline_id != self.pipeline_id
        ):
            errors['stage'] = 'A etapa não pertence ao pipeline informado.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def _validate_fk_brokerage(self, errors, field_name, related_object):
        if related_object is None or self.brokerage_id is None:
            return
        if related_object.brokerage_id != self.brokerage_id:
            errors[field_name] = 'Registro inválido para esta corretora.'


class DealStageHistory(TenantAwareModel):
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='stage_history',
    )
    from_stage = models.ForeignKey(
        Stage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
    )
    to_stage = models.ForeignKey(
        Stage,
        on_delete=models.PROTECT,
        related_name='+',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('-changed_at',)

    def __str__(self):
        return f'{self.deal} · {self.to_stage}'

    def clean(self):
        super().clean()
        errors = {}
        self._validate_fk_brokerage(
            errors,
            'deal',
            self.deal if self.deal_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'from_stage',
            self.from_stage if self.from_stage_id else None,
        )
        self._validate_fk_brokerage(
            errors,
            'to_stage',
            self.to_stage if self.to_stage_id else None,
        )
        if (
            self.changed_by_id
            and self.brokerage_id
            and self.changed_by.brokerage_id != self.brokerage_id
        ):
            errors['changed_by'] = 'Usuário inválido.'
        if (
            self.deal_id
            and self.to_stage_id
            and self.to_stage.pipeline_id != self.deal.pipeline_id
        ):
            errors['to_stage'] = 'A etapa não pertence ao pipeline da negociação.'
        if (
            self.deal_id
            and self.from_stage_id
            and self.from_stage.pipeline_id != self.deal.pipeline_id
        ):
            errors['from_stage'] = 'A etapa anterior não pertence ao pipeline.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def _validate_fk_brokerage(self, errors, field_name, related_object):
        if related_object is None or self.brokerage_id is None:
            return
        if related_object.brokerage_id != self.brokerage_id:
            errors[field_name] = 'Registro inválido para esta corretora.'
