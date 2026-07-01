from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class EntityType(models.TextChoices):
    PERSON = 'person', _('Pessoa Física')
    COMPANY = 'company', _('Pessoa Jurídica')


class Agent(TenantAwareModel):
    entity_type = models.CharField(
        max_length=10,
        choices=EntityType.choices,
        default=EntityType.PERSON,
    )
    name = models.CharField(max_length=200)
    document = models.CharField(max_length=18)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    susep_code = models.CharField(max_length=30, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_profiles',
        help_text='Vincule um usuário se o agente terá login na plataforma.',
    )
    default_commission_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text='Percentual padrão de repasse ao agente (ex.: 0.10 = 10%).',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'document'],
                name='agent_unique_document_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if (
            self.user_id
            and self.brokerage_id
            and self.user.brokerage_id != self.brokerage_id
        ):
            raise ValidationError({'user': 'Usuário inválido.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Producer(TenantAwareModel):
    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='producers',
        help_text='Vincule um agente ou deixe em branco para produtor direto.',
    )
    entity_type = models.CharField(
        max_length=10,
        choices=EntityType.choices,
        default=EntityType.PERSON,
    )
    name = models.CharField(max_length=200)
    document = models.CharField(max_length=18)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='producer_profiles',
        help_text='Vincule um usuário se o produtor terá login na plataforma.',
    )
    default_commission_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text='Percentual padrão de repasse ao produtor.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'document'],
                name='producer_unique_document_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'is_active']),
            models.Index(fields=['brokerage', 'agent']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.agent_id
            and self.brokerage_id
            and self.agent.brokerage_id != self.brokerage_id
        ):
            errors['agent'] = 'Agente inválido.'
        if (
            self.user_id
            and self.brokerage_id
            and self.user.brokerage_id != self.brokerage_id
        ):
            errors['user'] = 'Usuário inválido.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
