from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView

from base.mixins import RoleRequiredMixin
from notifications.models import Notification


@login_required
@require_GET
def unread_json(request):
    """Return unread notifications for the current user."""
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
    queryset = Notification.objects.filter(
        user=request.user,
        is_read=False,
        brokerage=tenant,
    )
    count = queryset.count()
    notifications = queryset.order_by('-created_at')[:20]
    return JsonResponse({
        'count': count,
        'items': [
            {
                'id': notification.id,
                'type': notification.type,
                'type_display': notification.get_type_display(),
                'title': notification.title,
                'message': notification.message,
                'url': notification.url,
                'created_at': notification.created_at.isoformat(),
            }
            for notification in notifications
        ],
    })


@login_required
@require_POST
def mark_read(request, pk):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
    queryset = Notification.objects.filter(
        user=request.user,
        pk=pk,
        brokerage=tenant,
    )
    notification = queryset.first()
    if notification is None:
        return JsonResponse(
            {'ok': False, 'error': 'Notificação não encontrada.'},
            status=404,
        )
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(
            update_fields=['is_read', 'read_at', 'updated_at'],
        )
    return JsonResponse({
        'ok': True,
        'id': notification.id,
        'url': notification.url or '',
    })


@login_required
@require_POST
def mark_all_read(request):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
    queryset = Notification.objects.filter(
        user=request.user,
        is_read=False,
        brokerage=tenant,
    )
    updated = queryset.update(is_read=True, read_at=timezone.now())
    return JsonResponse({'ok': True, 'updated': updated})


class NotificationListView(RoleRequiredMixin, ListView):
    template_name = 'notifications/notification_list.html'
    model = Notification
    context_object_name = 'notifications'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            brokerage=self.request.tenant,
        ).order_by('-created_at')
