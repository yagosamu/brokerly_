from django.contrib import admin

from crm.models import Deal, DealStageHistory, Pipeline, Stage


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'brokerage', 'created_at')
    list_filter = ('is_default', 'brokerage')
    search_fields = ('name',)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = (
        'pipeline',
        'name',
        'order',
        'is_won',
        'is_lost',
        'color',
        'brokerage',
    )
    list_filter = ('is_won', 'is_lost', 'brokerage')
    search_fields = ('name', 'pipeline__name')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'client',
        'pipeline',
        'stage',
        'status',
        'estimated_value',
        'expected_close_date',
        'brokerage',
    )
    list_filter = ('status', 'pipeline', 'stage', 'brokerage')
    search_fields = ('title', 'client__name', 'producer__name')


@admin.register(DealStageHistory)
class DealStageHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'deal',
        'from_stage',
        'to_stage',
        'changed_by',
        'changed_at',
    )
    list_filter = ('brokerage', 'to_stage')
