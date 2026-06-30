from django.contrib import admin

from claims.models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        'claim_number',
        'policy',
        'covered_item',
        'status',
        'occurrence_date',
        'notice_date',
        'claimed_amount',
        'approved_amount',
        'brokerage',
        'created_at',
    )
    list_filter = ('status', 'brokerage', 'occurrence_date')
    search_fields = (
        'claim_number',
        'policy__policy_number',
        'covered_item__description',
    )
    readonly_fields = (
        'ai_summary',
        'ai_summary_status',
        'ai_summary_updated_at',
        'created_at',
        'updated_at',
    )
    ordering = ('-occurrence_date',)
