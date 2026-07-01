from django.contrib import admin

from commissions.models import Commission, CommissionSplit


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        'policy',
        'base_premium',
        'insurer_rate',
        'insurer_amount',
        'status',
        'reference_date',
        'brokerage',
    )
    list_filter = ('status', 'brokerage', 'reference_date')
    search_fields = ('policy__policy_number',)
    ordering = ('-reference_date',)


@admin.register(CommissionSplit)
class CommissionSplitAdmin(admin.ModelAdmin):
    list_display = (
        'commission',
        'beneficiary_type',
        'agent',
        'producer',
        'rate',
        'amount',
        'status',
        'paid_at',
    )
    list_filter = ('beneficiary_type', 'status', 'brokerage')
