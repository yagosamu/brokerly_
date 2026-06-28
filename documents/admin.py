from django.contrib import admin

from documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'original_name',
        'brokerage',
        'content_type',
        'object_id',
        'mime_type',
        'size_kb',
        'uploaded_by',
        'created_at',
    )
    list_filter = ('mime_type', 'brokerage', 'content_type')
    search_fields = ('original_name', 'description', 'uploaded_by__email')
    readonly_fields = (
        'size_bytes',
        'mime_type',
        'uploaded_by',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)
