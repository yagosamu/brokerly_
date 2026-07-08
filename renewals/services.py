from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from insurance.models import CoveredItem, Policy
from renewals.models import Renewal


class RenewalError(ValueError):
    pass


@transaction.atomic
def ensure_renewal(policy):
    """Idempotent: return existing renewal or create a new pending one."""
    existing = Renewal.objects.filter(
        brokerage=policy.brokerage,
        policy=policy,
    ).first()
    if existing:
        return existing, False
    renewal = Renewal.objects.create(
        brokerage=policy.brokerage,
        policy=policy,
        due_date=policy.end_date,
        status=Renewal.Status.PENDING,
    )
    return renewal, True


@transaction.atomic
def renew_policy(*, renewal, new_policy_number, user):
    """Create a new Policy cloned from renewal.policy."""
    if renewal.status == Renewal.Status.RENEWED and renewal.new_policy_id:
        raise RenewalError('Esta renovação já foi concluída.')
    if not new_policy_number or not new_policy_number.strip():
        raise RenewalError('Informe o número da nova apólice.')
    new_policy_number = new_policy_number.strip()
    if Policy.objects.filter(
        brokerage=renewal.brokerage,
        policy_number=new_policy_number,
    ).exists():
        raise RenewalError(
            f'Já existe uma apólice com o número {new_policy_number} '
            'na sua corretora.'
        )

    original = renewal.policy
    start_date = (
        original.end_date + timedelta(days=1)
        if original.end_date
        else timezone.now().date()
    )
    end_date = start_date + timedelta(days=365)

    new_policy = Policy.objects.create(
        brokerage=original.brokerage,
        policy_number=new_policy_number,
        client=original.client,
        insurer=original.insurer,
        line_of_business=original.line_of_business,
        status=Policy.Status.ACTIVE,
        net_premium=original.net_premium,
        total_premium=original.total_premium,
        iof=original.iof,
        commission_rate=original.commission_rate,
        start_date=start_date,
        end_date=end_date,
        payment_info=original.payment_info,
        created_by=user,
    )
    cloned_items = [
        CoveredItem(
            brokerage=original.brokerage,
            proposal=None,
            policy=new_policy,
            item_type=item.item_type,
            description=item.description,
            identifier=item.identifier,
            insured_amount=item.insured_amount,
            attributes=dict(item.attributes or {}),
            coverages=list(item.coverages or []),
        )
        for item in original.covered_items.all()
    ]
    if cloned_items:
        CoveredItem.objects.bulk_create(cloned_items)

    original.status = Policy.Status.RENEWED
    original.save(update_fields=['status', 'updated_at'])

    renewal.new_policy = new_policy
    renewal.status = Renewal.Status.RENEWED
    renewal.save(update_fields=['new_policy', 'status', 'updated_at'])
    return new_policy
