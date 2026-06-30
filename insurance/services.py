from django.db import transaction

from insurance.models import CoveredItem, Policy, Proposal


class PolicyGenerationError(ValueError):
    """Raised when a policy cannot be generated from a proposal."""


@transaction.atomic
def generate_policy_from_proposal(*, proposal, policy_number, user):
    """Create a policy that mirrors the given proposal."""
    proposal = Proposal.objects.select_for_update().get(
        pk=proposal.pk,
        brokerage=proposal.brokerage,
    )
    if proposal.status == Proposal.Status.CONVERTED:
        raise PolicyGenerationError('Esta proposta já foi convertida em apólice.')
    if not policy_number or not policy_number.strip():
        raise PolicyGenerationError('Informe o número da apólice.')
    policy_number = policy_number.strip()

    if Policy.objects.filter(
        brokerage=proposal.brokerage,
        policy_number=policy_number,
    ).exists():
        raise PolicyGenerationError(
            f'Já existe uma apólice com o número {policy_number} na sua corretora.'
        )

    policy = Policy.objects.create(
        brokerage=proposal.brokerage,
        proposal=proposal,
        policy_number=policy_number,
        client=proposal.client,
        insurer=proposal.insurer,
        line_of_business=proposal.line_of_business,
        status=Policy.Status.ACTIVE,
        net_premium=proposal.net_premium,
        total_premium=proposal.total_premium,
        iof=proposal.iof,
        commission_rate=0,
        start_date=proposal.proposed_start_date,
        end_date=proposal.proposed_end_date,
        payment_info=proposal.payment_terms,
        created_by=user,
    )

    cloned = []
    for original in proposal.covered_items.all():
        cloned.append(
            CoveredItem(
                brokerage=proposal.brokerage,
                proposal=None,
                policy=policy,
                item_type=original.item_type,
                description=original.description,
                identifier=original.identifier,
                insured_amount=original.insured_amount,
                attributes=dict(original.attributes or {}),
                coverages=list(original.coverages or []),
            )
        )
    if cloned:
        CoveredItem.objects.bulk_create(cloned)

    proposal.status = Proposal.Status.CONVERTED
    proposal.save(update_fields=['status', 'updated_at'])

    return policy
