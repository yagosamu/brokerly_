from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from reports.registry import REPORTS


def clean_params(params):
    return {
        key: value
        for key, value in (params or {}).items()
        if value not in (None, '')
    }


def decimal_br(value):
    value = value or Decimal('0')
    return f'{value:.2f}'.replace('.', ',')


def date_br(value):
    if not value:
        return ''
    return value.strftime('%d/%m/%Y')


def int_param(params, key, default):
    try:
        value = int(params.get(key, default))
    except (TypeError, ValueError):
        return default
    return max(value, 1)


def date_range(params, default_days=365):
    today = timezone.now().date()
    start = parse_date(params.get('date_from', '') or '')
    end = parse_date(params.get('date_to', '') or '')
    if not end:
        end = today
    if not start:
        start = end - timedelta(days=default_days)
    return start, end


def brokerage_name(brokerage):
    return getattr(brokerage, 'trade_name', '') or str(brokerage)


def filename(report_type, extension):
    today = timezone.now().date().isoformat()
    return f'{report_type}-{today}.{extension}'


def metadata(report_type, brokerage, params):
    return {
        'title': REPORTS[report_type]['name'],
        'report_type': report_type,
        'brokerage_name': brokerage_name(brokerage),
        'brokerage_cnpj': getattr(brokerage, 'cnpj', ''),
        'generated_at': timezone.localtime(timezone.now()),
        'params': clean_params(params),
    }


def carteira_table(brokerage, params):
    from clients.models import Client
    from insurance.models import Policy

    status = params.get('status', 'active')
    queryset = Client.objects.filter(brokerage=brokerage)
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(is_active=False)

    rows = []
    for client in queryset.order_by('name'):
        policies = Policy.objects.filter(
            brokerage=brokerage,
            client=client,
            status='active',
        )
        rows.append([
            client.name,
            client.document,
            client.email,
            client.phone,
            policies.count(),
            decimal_br(policies.aggregate(total=Sum('total_premium'))['total']),
        ])
    return (
        ['Cliente', 'Documento', 'E-mail', 'Telefone', 'Apólices ativas', 'Prêmio'],
        rows,
    )


def propostas_table(brokerage, params):
    from insurance.models import Proposal

    start, end = date_range(params)
    queryset = Proposal.objects.filter(
        brokerage=brokerage,
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).select_related('client', 'insurer', 'line_of_business')
    queryset = _apply_common_filters(queryset, params)
    rows = [
        [
            proposal.number,
            date_br(proposal.created_at.date()),
            proposal.get_status_display(),
            proposal.client.name,
            proposal.insurer.name,
            proposal.line_of_business.name,
            decimal_br(proposal.total_premium),
        ]
        for proposal in queryset.order_by('-created_at')
    ]
    return (
        ['Número', 'Data', 'Status', 'Cliente', 'Seguradora', 'Ramo', 'Prêmio'],
        rows,
    )


def apolices_table(brokerage, params):
    from insurance.models import Policy

    start, end = date_range(params)
    queryset = Policy.objects.filter(brokerage=brokerage).select_related(
        'client',
        'insurer',
        'line_of_business',
    )
    queryset = queryset.filter(start_date__gte=start, start_date__lte=end)
    queryset = _apply_common_filters(queryset, params)
    rows = [
        [
            policy.policy_number,
            policy.get_status_display(),
            policy.client.name,
            policy.insurer.name,
            policy.line_of_business.name,
            date_br(policy.start_date),
            date_br(policy.end_date),
            decimal_br(policy.total_premium),
        ]
        for policy in queryset.order_by('-start_date', '-created_at')
    ]
    return (
        [
            'Número',
            'Status',
            'Cliente',
            'Seguradora',
            'Ramo',
            'Início',
            'Fim',
            'Prêmio',
        ],
        rows,
    )


def sinistros_table(brokerage, params):
    from claims.models import Claim

    start, end = date_range(params)
    queryset = Claim.objects.filter(
        brokerage=brokerage,
        occurrence_date__gte=start,
        occurrence_date__lte=end,
    ).select_related('policy', 'policy__client')
    if params.get('status'):
        queryset = queryset.filter(status=params['status'])
    rows = [
        [
            claim.claim_number,
            date_br(claim.occurrence_date),
            claim.get_status_display(),
            claim.policy.policy_number,
            claim.policy.client.name,
            decimal_br(claim.claimed_amount),
            decimal_br(claim.approved_amount),
        ]
        for claim in queryset.order_by('-occurrence_date')
    ]
    return (
        [
            'Número',
            'Ocorrência',
            'Status',
            'Apólice',
            'Cliente',
            'Reclamado',
            'Aprovado',
        ],
        rows,
    )


def renovacoes_table(brokerage, params):
    from renewals.models import Renewal

    today = timezone.now().date()
    horizon = today + timedelta(days=int_param(params, 'horizon_days', 90))
    queryset = Renewal.objects.filter(
        brokerage=brokerage,
        due_date__gte=today,
        due_date__lte=horizon,
    ).select_related('policy', 'policy__client')
    if params.get('status'):
        queryset = queryset.filter(status=params['status'])
    else:
        queryset = queryset.filter(status='pending')
    rows = [
        [
            renewal.policy.policy_number,
            renewal.policy.client.name,
            renewal.get_status_display(),
            date_br(renewal.due_date),
            (renewal.due_date - today).days,
            decimal_br(renewal.policy.total_premium),
        ]
        for renewal in queryset.order_by('due_date')
    ]
    return (
        ['Apólice', 'Cliente', 'Status', 'Vencimento', 'Dias restantes', 'Prêmio'],
        rows,
    )


def comissoes_table(brokerage, params):
    from commissions.models import Commission

    start, end = date_range(params)
    queryset = Commission.objects.filter(
        brokerage=brokerage,
        reference_date__gte=start,
        reference_date__lte=end,
    ).select_related('policy', 'policy__client')
    if params.get('status'):
        queryset = queryset.filter(status=params['status'])
    rows = [
        [
            commission.policy.policy_number,
            commission.policy.client.name,
            date_br(commission.reference_date),
            commission.get_status_display(),
            decimal_br(commission.base_premium),
            decimal_br(commission.insurer_amount),
        ]
        for commission in queryset.order_by('-reference_date')
    ]
    return (
        ['Apólice', 'Cliente', 'Referência', 'Status', 'Prêmio base', 'Comissão'],
        rows,
    )


def seguradoras_table(brokerage, params):
    from insurance.models import Policy

    limit = int_param(params, 'limit', 10)
    rows_qs = (
        Policy.objects.filter(brokerage=brokerage, status='active')
        .values('insurer__name')
        .annotate(policies=Count('id'), premium=Sum('total_premium'))
        .order_by('-premium')[:limit]
    )
    rows = [
        [
            row['insurer__name'],
            row['policies'],
            decimal_br(row['premium']),
        ]
        for row in rows_qs
    ]
    return ['Seguradora', 'Apólices ativas', 'Prêmio'], rows


def produtividade_table(brokerage, params):
    from crm.models import Deal

    start, end = date_range(params)
    limit = int_param(params, 'limit', 10)
    producer_rows = (
        Deal.objects.filter(
            brokerage=brokerage,
            status='won',
            created_at__date__gte=start,
            created_at__date__lte=end,
        )
        .values('producer__name')
        .annotate(deals=Count('id'), value=Sum('estimated_value'))
        .order_by('-deals', '-value')[:limit]
    )
    rows = [
        ['Produtor', row['producer__name'], row['deals'], decimal_br(row['value'])]
        for row in producer_rows
    ]

    agent_rows = (
        Deal.objects.filter(
            brokerage=brokerage,
            status='won',
            agent__isnull=False,
            created_at__date__gte=start,
            created_at__date__lte=end,
        )
        .values('agent__name')
        .annotate(deals=Count('id'), value=Sum('estimated_value'))
        .order_by('-deals', '-value')[:limit]
    )
    rows.extend([
        ['Agente', row['agent__name'], row['deals'], decimal_br(row['value'])]
        for row in agent_rows
    ])
    return ['Tipo', 'Nome', 'Negócios ganhos', 'Valor estimado'], rows


TABLE_BUILDERS = {
    'carteira': carteira_table,
    'propostas': propostas_table,
    'apolices': apolices_table,
    'sinistros': sinistros_table,
    'renovacoes': renovacoes_table,
    'comissoes': comissoes_table,
    'seguradoras': seguradoras_table,
    'produtividade': produtividade_table,
}


def report_table(report_type, brokerage, params):
    headers, rows = TABLE_BUILDERS[report_type](brokerage, clean_params(params))
    return metadata(report_type, brokerage, params), headers, rows


def _apply_common_filters(queryset, params):
    if params.get('insurer_id'):
        queryset = queryset.filter(insurer_id=params['insurer_id'])
    if params.get('line_of_business_id'):
        queryset = queryset.filter(line_of_business_id=params['line_of_business_id'])
    if params.get('status'):
        queryset = queryset.filter(status=params['status'])
    return queryset
