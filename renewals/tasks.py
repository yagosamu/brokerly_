from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from insurance.models import Policy
from notifications.models import Notification
from renewals.services import ensure_renewal


@shared_task(name='renewals.check_upcoming_renewals')
def check_upcoming_renewals():
    """Find policies expiring in up to 90 days and create renewals."""
    today = timezone.now().date()
    horizon = today + timedelta(days=90)
    queryset = Policy.objects.filter(
        status=Policy.Status.ACTIVE,
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=horizon,
    ).select_related('brokerage', 'client')
    created_count = 0
    checked_count = queryset.count()
    for policy in queryset:
        renewal, is_new = ensure_renewal(policy)
        if not is_new:
            continue
        created_count += 1
        owner = policy.brokerage.owner
        days_left = (policy.end_date - today).days
        Notification.objects.create(
            brokerage=policy.brokerage,
            user=owner,
            type=Notification.Type.RENEWAL,
            title=f'Renovação em {days_left} dias · {policy.client.name}',
            message=(
                f'Apólice #{policy.policy_number} vence em '
                f'{policy.end_date.strftime("%d/%m/%Y")}.'
            ),
            url=f'/renovacoes/{renewal.id}/',
        )
    return {'checked': checked_count, 'created': created_count}


@shared_task(name='renewals.expire_policies')
def expire_policies():
    """Mark active policies past end_date as expired."""
    today = timezone.now().date()
    updated = Policy.objects.filter(
        status=Policy.Status.ACTIVE,
        end_date__isnull=False,
        end_date__lt=today,
    ).update(status=Policy.Status.EXPIRED)
    return {'expired': updated}
