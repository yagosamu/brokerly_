from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.managers import UserManager
from base.models import BaseModel


class User(AbstractUser, BaseModel):
    class Role(models.TextChoices):
        OWNER = 'owner', _('Administrador')
        MANAGER = 'manager', _('Gerente')
        BROKER = 'broker', _('Corretor')
        AGENT = 'agent', _('Agente')
        PRODUCER = 'producer', _('Produtor')
        OPERATIONAL = 'operational', _('Operacional')

    username = None
    email = models.EmailField('email address', unique=True)
    brokerage = models.ForeignKey(
        'tenants.Brokerage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATIONAL,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
