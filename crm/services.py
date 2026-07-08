from django.db import transaction

from crm.models import Deal, DealStageHistory, Pipeline, Stage


DEFAULT_STAGES = [
    {
        'name': 'Novo lead',
        'color': '#6b7885',
        'order': 1,
        'is_won': False,
        'is_lost': False,
    },
    {
        'name': 'Em contato',
        'color': '#3454d1',
        'order': 2,
        'is_won': False,
        'is_lost': False,
    },
    {
        'name': 'Cotação',
        'color': '#ffa21d',
        'order': 3,
        'is_won': False,
        'is_lost': False,
    },
    {
        'name': 'Proposta enviada',
        'color': '#3dc7be',
        'order': 4,
        'is_won': False,
        'is_lost': False,
    },
    {
        'name': 'Ganho',
        'color': '#17c666',
        'order': 5,
        'is_won': True,
        'is_lost': False,
    },
    {
        'name': 'Perdido',
        'color': '#ea4d4d',
        'order': 6,
        'is_won': False,
        'is_lost': True,
    },
]


@transaction.atomic
def seed_default_pipeline(brokerage):
    pipeline, _ = Pipeline.objects.get_or_create(
        brokerage=brokerage,
        name='Negociações',
        defaults={'is_default': True},
    )
    for stage_data in DEFAULT_STAGES:
        Stage.objects.get_or_create(
            brokerage=brokerage,
            pipeline=pipeline,
            name=stage_data['name'],
            defaults={
                'color': stage_data['color'],
                'order': stage_data['order'],
                'is_won': stage_data['is_won'],
                'is_lost': stage_data['is_lost'],
            },
        )
    return pipeline


@transaction.atomic
def move_deal_to_stage(*, deal, target_stage, user, note=''):
    """Move deal to another stage, log history, and sync status."""
    if target_stage.pipeline_id != deal.pipeline_id:
        raise ValueError('A etapa não pertence ao pipeline da negociação.')
    if target_stage.brokerage_id != deal.brokerage_id:
        raise ValueError('Etapa inválida.')

    from_stage = deal.stage
    if from_stage.id == target_stage.id:
        return deal

    DealStageHistory.objects.create(
        brokerage=deal.brokerage,
        deal=deal,
        from_stage=from_stage,
        to_stage=target_stage,
        changed_by=user,
        note=note,
    )
    deal.stage = target_stage
    if target_stage.is_won:
        deal.status = Deal.Status.WON
    elif target_stage.is_lost:
        deal.status = Deal.Status.LOST
    else:
        deal.status = Deal.Status.OPEN
    deal.save(update_fields=['stage', 'status', 'updated_at'])
    return deal
