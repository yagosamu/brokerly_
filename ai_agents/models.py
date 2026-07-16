from django.conf import settings
from django.db import models

from base.models import BaseModel, TenantAwareModel


class ChatSession(TenantAwareModel):
    """A conversation thread owned by a user within a brokerage."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    title = models.CharField(max_length=120, default='Nova conversa')
    is_archived = models.BooleanField(default=False)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-last_message_at', '-created_at')
        indexes = [
            models.Index(fields=('brokerage', 'user', '-last_message_at')),
        ]

    def __str__(self):
        return f'{self.title} · {self.user_id}'


class ChatMessage(BaseModel):
    """A single message within a ChatSession."""

    class Role(models.TextChoices):
        USER = 'user', 'Usuário'
        ASSISTANT = 'assistant', 'Assistente'
        SYSTEM = 'system', 'Sistema'
        TOOL = 'tool', 'Ferramenta'

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    tool_calls = models.JSONField(null=True, blank=True)
    token_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ('created_at',)
        indexes = [models.Index(fields=('session', 'created_at'))]
