from django.contrib import admin

from insurers.models import Insurer, LineOfBusiness


@admin.register(Insurer)
class InsurerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cnpj',
        'susep_code',
        'brokerage',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'brokerage')
    search_fields = ('name', 'cnpj', 'susep_code')
    ordering = ('name',)


@admin.register(LineOfBusiness)
class LineOfBusinessAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'category',
        'brokerage',
        'is_active',
        'created_at',
    )
    list_filter = ('category', 'is_active', 'brokerage')
    search_fields = ('name', 'code')
    ordering = ('name',)
