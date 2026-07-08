from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'type',
        'user',
        'is_read',
        'created_at',
        'brokerage',
    )
    list_filter = ('type', 'is_read', 'brokerage')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('read_at', 'created_at', 'updated_at')
    ordering = ('-created_at',)
