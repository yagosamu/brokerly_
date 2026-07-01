from django.contrib import admin

from partners.models import Agent, Producer


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'entity_type',
        'document',
        'default_commission_rate',
        'is_active',
        'brokerage',
        'created_at',
    )
    list_filter = ('entity_type', 'is_active', 'brokerage')
    search_fields = ('name', 'document', 'email', 'susep_code')
    ordering = ('name',)


@admin.register(Producer)
class ProducerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'entity_type',
        'document',
        'agent',
        'default_commission_rate',
        'is_active',
        'brokerage',
        'created_at',
    )
    list_filter = ('entity_type', 'is_active', 'brokerage', 'agent')
    search_fields = ('name', 'document', 'email')
    ordering = ('name',)
