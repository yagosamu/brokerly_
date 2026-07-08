"""Tenant-scoped tool factories for summary agents."""

from langchain_core.tools import tool


def _date(value):
    return value.isoformat() if value else None


def build_client_tools(brokerage, entity_id):
    from claims.models import Claim
    from clients.models import Client
    from insurance.models import Policy, Proposal

    @tool
    def get_client_info() -> dict:
        """Return the client's basic info."""
        try:
            client = Client.objects.get(pk=entity_id, brokerage=brokerage)
        except Client.DoesNotExist:
            return {}
        return {
            'name': client.name,
            'trade_name': client.trade_name,
            'person_type': client.get_person_type_display(),
            'document': client.document,
            'email': client.email,
            'phone': client.phone,
            'city': client.city,
            'state': client.state,
            'is_active': client.is_active,
            'created_at': _date(client.created_at.date()),
        }

    @tool
    def list_client_policies() -> list[dict]:
        """List policies of the client with insurer, values, and dates."""
        queryset = Policy.objects.filter(
            brokerage=brokerage,
            client_id=entity_id,
        ).select_related('insurer', 'line_of_business')[:20]
        return [
            {
                'policy_number': policy.policy_number,
                'insurer': policy.insurer.name,
                'line_of_business': policy.line_of_business.name,
                'status': policy.get_status_display(),
                'net_premium': str(policy.net_premium),
                'total_premium': str(policy.total_premium),
                'start_date': _date(policy.start_date),
                'end_date': _date(policy.end_date),
            }
            for policy in queryset
        ]

    @tool
    def list_client_proposals() -> list[dict]:
        """List proposals of the client with status, insurer, and values."""
        queryset = Proposal.objects.filter(
            brokerage=brokerage,
            client_id=entity_id,
        ).select_related('insurer', 'line_of_business')[:20]
        return [
            {
                'number': proposal.number,
                'status': proposal.get_status_display(),
                'insurer': proposal.insurer.name,
                'line_of_business': proposal.line_of_business.name,
                'total_premium': str(proposal.total_premium),
                'created_at': _date(proposal.created_at.date()),
            }
            for proposal in queryset
        ]

    @tool
    def list_client_claims() -> list[dict]:
        """List claims linked to this client's policies."""
        queryset = Claim.objects.filter(
            brokerage=brokerage,
            policy__client_id=entity_id,
        ).select_related('policy')[:20]
        return [
            {
                'claim_number': claim.claim_number,
                'policy_number': claim.policy.policy_number,
                'status': claim.get_status_display(),
                'occurrence_date': _date(claim.occurrence_date),
                'claimed_amount': str(claim.claimed_amount),
                'approved_amount': str(claim.approved_amount),
            }
            for claim in queryset
        ]

    return [
        get_client_info,
        list_client_policies,
        list_client_proposals,
        list_client_claims,
    ]


def build_policy_tools(brokerage, entity_id):
    from claims.models import Claim
    from insurance.models import CoveredItem, Endorsement, Policy

    @tool
    def get_policy_info() -> dict:
        """Return the policy header."""
        try:
            policy = Policy.objects.select_related(
                'client',
                'insurer',
                'line_of_business',
            ).get(pk=entity_id, brokerage=brokerage)
        except Policy.DoesNotExist:
            return {}
        return {
            'policy_number': policy.policy_number,
            'status': policy.get_status_display(),
            'client_name': policy.client.name,
            'insurer': policy.insurer.name,
            'line_of_business': policy.line_of_business.name,
            'net_premium': str(policy.net_premium),
            'total_premium': str(policy.total_premium),
            'iof': str(policy.iof),
            'commission_rate': str(policy.commission_rate),
            'start_date': _date(policy.start_date),
            'end_date': _date(policy.end_date),
        }

    @tool
    def list_covered_items() -> list[dict]:
        """List covered items of the policy."""
        queryset = CoveredItem.objects.filter(
            brokerage=brokerage,
            policy_id=entity_id,
        )[:30]
        return [
            {
                'type': item.get_item_type_display(),
                'description': item.description,
                'identifier': item.identifier,
                'insured_amount': str(item.insured_amount),
                'coverages': item.coverages or [],
            }
            for item in queryset
        ]

    @tool
    def list_policy_claims() -> list[dict]:
        """List claims filed against this policy."""
        queryset = Claim.objects.filter(
            brokerage=brokerage,
            policy_id=entity_id,
        )[:20]
        return [
            {
                'claim_number': claim.claim_number,
                'status': claim.get_status_display(),
                'occurrence_date': _date(claim.occurrence_date),
                'claimed_amount': str(claim.claimed_amount),
                'approved_amount': str(claim.approved_amount),
            }
            for claim in queryset
        ]

    @tool
    def list_policy_endorsements() -> list[dict]:
        """List endorsements applied to this policy."""
        queryset = Endorsement.objects.filter(
            brokerage=brokerage,
            policy_id=entity_id,
        )[:20]
        return [
            {
                'endorsement_number': endorsement.endorsement_number,
                'type': endorsement.get_type_display(),
                'status': endorsement.get_status_display(),
                'effective_date': _date(endorsement.effective_date),
                'premium_change': str(endorsement.premium_change),
            }
            for endorsement in queryset
        ]

    return [
        get_policy_info,
        list_covered_items,
        list_policy_claims,
        list_policy_endorsements,
    ]


def build_proposal_tools(brokerage, entity_id):
    from insurance.models import CoveredItem, Proposal

    @tool
    def get_proposal_info() -> dict:
        """Return proposal basic information."""
        try:
            proposal = Proposal.objects.select_related(
                'client',
                'insurer',
                'line_of_business',
            ).get(pk=entity_id, brokerage=brokerage)
        except Proposal.DoesNotExist:
            return {}
        return {
            'number': proposal.number,
            'status': proposal.get_status_display(),
            'client_name': proposal.client.name,
            'insurer': proposal.insurer.name,
            'line_of_business': proposal.line_of_business.name,
            'net_premium': str(proposal.net_premium),
            'total_premium': str(proposal.total_premium),
            'notes': proposal.notes,
        }

    @tool
    def list_proposal_items() -> list[dict]:
        """List covered items attached to this proposal."""
        queryset = CoveredItem.objects.filter(
            brokerage=brokerage,
            proposal_id=entity_id,
        )[:30]
        return [
            {
                'type': item.get_item_type_display(),
                'description': item.description,
                'insured_amount': str(item.insured_amount),
                'coverages': item.coverages or [],
            }
            for item in queryset
        ]

    return [get_proposal_info, list_proposal_items]


def build_claim_tools(brokerage, entity_id):
    from claims.models import Claim

    @tool
    def get_claim_info() -> dict:
        """Return claim information."""
        try:
            claim = Claim.objects.select_related(
                'policy',
                'policy__client',
                'covered_item',
            ).get(pk=entity_id, brokerage=brokerage)
        except Claim.DoesNotExist:
            return {}
        return {
            'claim_number': claim.claim_number,
            'status': claim.get_status_display(),
            'policy_number': claim.policy.policy_number,
            'client_name': claim.policy.client.name,
                'covered_item': (
                    claim.covered_item.description if claim.covered_item else None
                ),
            'occurrence_date': _date(claim.occurrence_date),
            'notice_date': _date(claim.notice_date),
            'description': claim.description,
            'claimed_amount': str(claim.claimed_amount),
            'approved_amount': str(claim.approved_amount),
        }

    return [get_claim_info]


def build_deal_tools(brokerage, entity_id):
    from crm.models import Deal, DealStageHistory

    @tool
    def get_deal_info() -> dict:
        """Return CRM deal information."""
        try:
            deal = Deal.objects.select_related(
                'pipeline',
                'stage',
                'client',
                'producer',
                'agent',
                'insurer',
                'line_of_business',
            ).get(pk=entity_id, brokerage=brokerage)
        except Deal.DoesNotExist:
            return {}
        return {
            'title': deal.title,
            'pipeline': deal.pipeline.name,
            'stage': deal.stage.name,
            'status': deal.get_status_display(),
            'client_name': deal.client.name if deal.client else None,
            'producer': deal.producer.name if deal.producer else None,
            'agent': deal.agent.name if deal.agent else None,
            'insurer': deal.insurer.name if deal.insurer else None,
            'line_of_business': (
                deal.line_of_business.name if deal.line_of_business else None
            ),
            'estimated_value': str(deal.estimated_value),
            'expected_close_date': _date(deal.expected_close_date),
            'description': deal.description,
        }

    @tool
    def list_deal_stage_history() -> list[dict]:
        """List stage changes for this CRM deal."""
        queryset = DealStageHistory.objects.filter(
            brokerage=brokerage,
            deal_id=entity_id,
        ).select_related('from_stage', 'to_stage')[:20]
        return [
            {
                'from_stage': (
                    history.from_stage.name if history.from_stage else None
                ),
                'to_stage': history.to_stage.name,
                'changed_at': history.changed_at.isoformat(),
                'note': history.note,
            }
            for history in queryset
        ]

    return [get_deal_info, list_deal_stage_history]


TOOL_BUILDERS = {
    'client': build_client_tools,
    'policy': build_policy_tools,
    'proposal': build_proposal_tools,
    'claim': build_claim_tools,
    'deal': build_deal_tools,
}


def build_tenant_tools(brokerage, entity_type, entity_id):
    """Build tools for an entity without exposing tenant selection to the LLM."""
    return TOOL_BUILDERS[entity_type](brokerage, entity_id)
