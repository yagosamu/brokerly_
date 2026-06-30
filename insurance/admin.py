from django.contrib import admin

from insurance.models import CoveredItem, Policy, Proposal


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'client',
        'insurer',
        'line_of_business',
        'status',
        'total_premium',
        'brokerage',
        'created_at',
    )
    list_filter = ('status', 'insurer', 'line_of_business', 'brokerage')
    search_fields = ('number', 'client__name', 'client__document')
    ordering = ('-created_at',)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = (
        'policy_number',
        'client',
        'insurer',
        'status',
        'start_date',
        'end_date',
        'total_premium',
    )
    list_filter = ('status', 'brokerage', 'insurer')
    search_fields = ('policy_number', 'client__name', 'client__document')
    ordering = ('-created_at',)


@admin.register(CoveredItem)
class CoveredItemAdmin(admin.ModelAdmin):
    list_display = (
        'description',
        'item_type',
        'identifier',
        'insured_amount',
        'proposal',
        'policy',
        'brokerage',
    )
    list_filter = ('item_type',)
    search_fields = ('description', 'identifier')
