from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager
from base.models import BaseModel


class User(AbstractUser, BaseModel):
    username = None
    email = models.EmailField('email address', unique=True)
    brokerage = models.ForeignKey(
        'tenants.Brokerage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
