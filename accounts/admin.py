from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            'Informações pessoais',
            {'fields': ('first_name', 'last_name', 'brokerage', 'role')},
        ),
        (
            'Permissões',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'brokerage',
                    'role',
                    'is_staff',
                    'is_active',
                ),
            },
        ),
    )
    list_display = (
        'email',
        'first_name',
        'last_name',
        'brokerage',
        'role',
        'is_active',
        'is_staff',
    )
    list_filter = ('role', 'brokerage', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'brokerage__legal_name')
    ordering = ('email',)
