from django.contrib import admin

from renewals.models import Renewal


@admin.register(Renewal)
class RenewalAdmin(admin.ModelAdmin):
    list_display = (
        'policy',
        'new_policy',
        'status',
        'due_date',
        'brokerage',
        'created_at',
    )
    list_filter = ('status', 'due_date', 'brokerage')
    search_fields = (
        'policy__policy_number',
        'new_policy__policy_number',
        'policy__client__name',
        'notes',
    )
    ordering = ('due_date',)
