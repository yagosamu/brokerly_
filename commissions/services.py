from decimal import Decimal

from django.db import transaction

from commissions.models import Commission


@transaction.atomic
def generate_commission_for_policy(policy):
    """Create or return the existing commission for a policy."""
    existing = Commission.objects.filter(policy=policy).first()
    if existing is not None:
        return existing
    base = policy.net_premium or Decimal('0')
    rate = policy.commission_rate or Decimal('0')
    amount = (base * rate).quantize(Decimal('0.01'))
    return Commission.objects.create(
        brokerage=policy.brokerage,
        policy=policy,
        base_premium=base,
        insurer_rate=rate,
        insurer_amount=amount,
        status=Commission.Status.PENDING,
        reference_date=policy.start_date or policy.created_at.date(),
    )


def calculate_split_amount(commission, rate):
    """Calculate a split from the insurer commission amount and a rate."""
    effective_rate = rate or Decimal('0')
    return (commission.insurer_amount * effective_rate).quantize(
        Decimal('0.01')
    )
