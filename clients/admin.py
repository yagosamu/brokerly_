from django.contrib import admin

from clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'person_type',
        'document',
        'email',
        'brokerage',
        'is_active',
        'created_at',
    )
    list_filter = ('person_type', 'is_active', 'brokerage')
    search_fields = ('name', 'trade_name', 'document', 'email')
    readonly_fields = (
        'ai_summary',
        'ai_summary_status',
        'ai_summary_updated_at',
        'created_at',
        'updated_at',
    )
    ordering = ('name',)
