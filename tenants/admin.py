from django.contrib import admin

from tenants.models import Brokerage, Plan, Subscription


@admin.register(Brokerage)
class BrokerageAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'cnpj', 'owner', 'plan', 'is_active')
    search_fields = ('legal_name', 'trade_name', 'cnpj', 'susep_code')
    list_filter = ('is_active', 'plan', 'state')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'is_available')
    search_fields = ('name', 'slug')
    list_filter = ('is_available',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('brokerage', 'plan', 'status', 'started_at', 'expires_at')
    list_filter = ('status', 'plan')
    search_fields = ('brokerage__legal_name', 'brokerage__cnpj')
