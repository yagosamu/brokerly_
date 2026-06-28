from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from base.models import TenantAwareModel
from documents.storage import document_upload_path


class Document(TenantAwareModel):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    file = models.FileField(upload_to=document_upload_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.PositiveBigIntegerField()
    description = models.CharField(max_length=255, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
    )

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'brokerage']),
        ]

    def __str__(self):
        return self.original_name

    @property
    def size_kb(self):
        return round(self.size_bytes / 1024, 1)
