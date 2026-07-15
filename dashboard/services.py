from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone


def _period_range(period, date_from=None, date_to=None):
    today = timezone.now().date()
    if period == 'custom' and date_from and date_to:
        return date_from, date_to
    if period == 'ytd':
        return date(today.year, 1, 1), today
    days_map = {'30d': 30, '60d': 60, '90d': 90}
    days = days_map.get(period, 30)
    return today - timedelta(days=days), today


def _month_start(value):
    if hasattr(value, 'date'):
        value = value.date()
    return value.replace(day=1)


def kpi_counters(brokerage, start, end):
    from claims.models import Claim
    from clients.models import Client
    from commissions.models import Commission
    from insurance.models import Policy, Proposal
    from renewals.models import Renewal

    today = timezone.now().date()
    renewal_horizon = today + timedelta(days=30)

    active_policies = Policy.objects.filter(brokerage=brokerage, status='active')
    open_claims = Claim.objects.filter(
        brokerage=brokerage,
    ).exclude(status__in=('closed', 'paid'))
    renewals_30d = Renewal.objects.filter(
        brokerage=brokerage,
        status='pending',
        due_date__gte=today,
        due_date__lte=renewal_horizon,
    )
    pending_commissions = Commission.objects.filter(
        brokerage=brokerage,
        status='pending',
    )
    clients_total = Client.objects.filter(
        brokerage=brokerage,
        is_active=True,
    ).count()
    proposals_in_period = Proposal.objects.filter(
        brokerage=brokerage,
        created_at__date__gte=start,
        created_at__date__lte=end,
    )

    return {
        'clients_total': clients_total,
        'proposals_count': proposals_in_period.count(),
        'active_policies_count': active_policies.count(),
        'active_policies_premium': active_policies.aggregate(
            total=Sum('total_premium'),
        )['total'] or Decimal('0'),
        'open_claims_count': open_claims.count(),
        'renewals_next_30d_count': renewals_30d.count(),
        'pending_commissions_total': pending_commissions.aggregate(
            total=Sum('insurer_amount'),
        )['total'] or Decimal('0'),
    }


def funnel_data(brokerage):
    """Return deals count by stage of the default pipeline."""
    from crm.models import Deal, Pipeline

    pipeline = Pipeline.objects.filter(brokerage=brokerage, is_default=True).first()
    if not pipeline:
        pipeline = Pipeline.objects.filter(brokerage=brokerage).first()
    if not pipeline:
        return {'pipeline_name': None, 'stages': []}

    stages = pipeline.stages.order_by('order', 'id')
    deals_qs = Deal.objects.filter(brokerage=brokerage, pipeline=pipeline)
    counts_by_stage = {stage.id: 0 for stage in stages}
    for row in deals_qs.values('stage_id').annotate(count=Count('id')):
        counts_by_stage[row['stage_id']] = row['count']

    return {
        'pipeline_name': pipeline.name,
        'stages': [
            {
                'name': stage.name,
                'color': stage.color,
                'count': counts_by_stage.get(stage.id, 0),
            }
            for stage in stages
        ],
    }


def monthly_premium_series(brokerage, months=12):
    """Return premium and commission totals grouped by month."""
    from commissions.models import Commission
    from insurance.models import Policy

    today = timezone.now().date()
    first_of_current = today.replace(day=1)
    year = first_of_current.year
    month = first_of_current.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)

    rows = (
        Policy.objects.filter(
            brokerage=brokerage,
            created_at__date__gte=start,
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_premium'))
        .order_by('month')
    )
    commission_rows = (
        Commission.objects.filter(
            brokerage=brokerage,
            reference_date__gte=start,
        )
        .annotate(month=TruncMonth('reference_date'))
        .values('month')
        .annotate(total=Sum('insurer_amount'))
        .order_by('month')
    )
    by_month = {
        _month_start(row['month']): row['total'] or Decimal('0')
        for row in rows
    }
    commission_by_month = {
        _month_start(row['month']): row['total'] or Decimal('0')
        for row in commission_rows
    }
    series = []
    cursor = start
    for _ in range(months):
        series.append({
            'month': cursor.isoformat(),
            'total': by_month.get(cursor, Decimal('0')),
            'commission_total': commission_by_month.get(cursor, Decimal('0')),
        })
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return series


def policies_by_line(brokerage, start, end):
    from insurance.models import Policy

    rows = (
        Policy.objects.filter(
            brokerage=brokerage,
            created_at__date__gte=start,
            created_at__date__lte=end,
        )
        .values('line_of_business__id', 'line_of_business__name')
        .annotate(count=Count('id'), premium=Sum('total_premium'))
        .order_by('-count', 'line_of_business__name')
    )
    return [
        {
            'line_of_business_id': row['line_of_business__id'],
            'line_of_business_name': row['line_of_business__name'],
            'count': row['count'],
            'premium': row['premium'] or Decimal('0'),
        }
        for row in rows
    ]


def claims_by_status(brokerage, start, end):
    from claims.models import Claim

    rows = (
        Claim.objects.filter(
            brokerage=brokerage,
            occurrence_date__gte=start,
            occurrence_date__lte=end,
        )
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    label_map = dict(Claim.Status.choices)
    return [
        {
            'status': row['status'],
            'label': label_map.get(row['status'], row['status']),
            'count': row['count'],
        }
        for row in rows
    ]


def top_insurers(brokerage, limit=5):
    from insurance.models import Policy

    rows = (
        Policy.objects.filter(brokerage=brokerage, status='active')
        .values('insurer__id', 'insurer__name')
        .annotate(policies=Count('id'), premium=Sum('total_premium'))
        .order_by('-premium')[:limit]
    )
    return [
        {
            'insurer_id': row['insurer__id'],
            'insurer_name': row['insurer__name'],
            'policies': row['policies'],
            'premium': row['premium'] or Decimal('0'),
        }
        for row in rows
    ]


def top_producers(brokerage, limit=5):
    """Return top producers by count of won deals as proxy for closed sales."""
    from crm.models import Deal

    rows = (
        Deal.objects.filter(brokerage=brokerage, status='won')
        .values('producer__id', 'producer__name')
        .annotate(deals=Count('id'), value=Sum('estimated_value'))
        .order_by('-deals')[:limit]
    )
    return [
        {
            'producer_id': row['producer__id'],
            'producer_name': row['producer__name'],
            'deals': row['deals'],
            'value': row['value'] or Decimal('0'),
        }
        for row in rows
    ]


def upcoming_renewals(brokerage, limit=5, horizon_days=90):
    from renewals.models import Renewal

    today = timezone.now().date()
    horizon = today + timedelta(days=horizon_days)
    qs = (
        Renewal.objects.filter(
            brokerage=brokerage,
            status='pending',
            due_date__gte=today,
            due_date__lte=horizon,
        )
        .select_related('policy', 'policy__client')
        .order_by('due_date')[:limit]
    )
    return [
        {
            'id': renewal.id,
            'policy_number': renewal.policy.policy_number,
            'client_name': renewal.policy.client.name,
            'due_date': renewal.due_date,
            'days_left': (renewal.due_date - today).days,
            'total_premium': renewal.policy.total_premium,
        }
        for renewal in qs
    ]


def rule_based_insights(brokerage, kpis, funnel, renewals):
    """Return simple text insights derived from raw aggregates."""
    output = []
    if kpis['renewals_next_30d_count'] > 0:
        output.append({
            'level': 'warning',
            'icon': 'clock',
            'text': (
                f"{kpis['renewals_next_30d_count']} apólice(s) vencem nos "
                'próximos 30 dias.'
            ),
        })
    if kpis['pending_commissions_total'] and kpis['pending_commissions_total'] > 0:
        output.append({
            'level': 'info',
            'icon': 'dollar-sign',
            'text': (
                f"R$ {kpis['pending_commissions_total']:.2f} em comissões "
                'pendentes de recebimento.'
            ),
        })
    if kpis['open_claims_count'] > 0:
        output.append({
            'level': 'danger' if kpis['open_claims_count'] > 5 else 'info',
            'icon': 'alert-circle',
            'text': (
                f"{kpis['open_claims_count']} sinistro(s) em aberto para "
                'acompanhamento.'
            ),
        })
    if not funnel['stages'] or all(stage['count'] == 0 for stage in funnel['stages']):
        output.append({
            'level': 'info',
            'icon': 'layout',
            'text': 'Ainda não há negociações no funil. Adicione oportunidades no CRM.',
        })
    return output
