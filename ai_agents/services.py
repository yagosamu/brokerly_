"""Summary generation services for tenant-scoped entities."""

from django.apps import apps
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification

from .agent import run_summary_agent


ENTITY_MODELS = {
    'client': ('clients', 'Client'),
    'policy': ('insurance', 'Policy'),
    'proposal': ('insurance', 'Proposal'),
    'claim': ('claims', 'Claim'),
    'deal': ('crm', 'Deal'),
}

ENTITY_URL_TEMPLATES = {
    'client': 'clients:client_detail',
    'policy': 'insurance:policy_detail',
    'proposal': 'insurance:proposal_detail',
    'claim': 'claims:claim_detail',
    'deal': 'crm:deal_detail',
}

ENTITY_LABELS = {
    'client': 'cliente',
    'policy': 'apólice',
    'proposal': 'proposta',
    'claim': 'sinistro',
    'deal': 'negociação',
}


def get_entity_model(entity_type):
    app_label, model_name = ENTITY_MODELS[entity_type]
    return apps.get_model(app_label, model_name)


def _get_entity(entity_type, entity_id, brokerage):
    model = get_entity_model(entity_type)
    return model.objects.get(pk=entity_id, brokerage=brokerage)


def _entity_display_title(entity):
    for field_name in ('name', 'policy_number', 'number', 'claim_number', 'title'):
        value = getattr(entity, field_name, None)
        if value:
            return str(value)
    return str(entity)


def _summary_fields(now=None):
    return {
        'ai_summary_status': 'error',
        'ai_summary_updated_at': now or timezone.now(),
    }


def mark_summary_error(entity_type, entity_id, brokerage, error):
    entity = _get_entity(entity_type, entity_id, brokerage)
    message = str(error)[:500] or 'Erro ao gerar resumo.'
    fields = _summary_fields()
    entity.ai_summary = f'Erro ao gerar resumo: {message}'
    entity.ai_summary_status = fields['ai_summary_status']
    entity.ai_summary_updated_at = fields['ai_summary_updated_at']
    entity.save(update_fields=[
        'ai_summary',
        'ai_summary_status',
        'ai_summary_updated_at',
        'updated_at',
    ])
    return entity


def start_summary_processing(entity):
    entity.ai_summary_status = 'processing'
    entity.save(update_fields=['ai_summary_status', 'updated_at'])


def generate_summary(entity_type, entity_id, brokerage, user):
    entity = _get_entity(entity_type, entity_id, brokerage)
    start_summary_processing(entity)
    try:
        result = run_summary_agent(entity_type, entity_id, brokerage)
        markdown = result['markdown'] or 'Não foi possível gerar um resumo.'
        entity.ai_summary = markdown
        entity.ai_summary_status = 'done'
        entity.ai_summary_updated_at = timezone.now()
        entity.save(update_fields=[
            'ai_summary',
            'ai_summary_status',
            'ai_summary_updated_at',
            'updated_at',
        ])
        Notification.objects.create(
            brokerage=brokerage,
            user=user,
            type=Notification.Type.AI_SUMMARY,
            title='Resumo de IA concluído',
            message=(
                f'O resumo da {ENTITY_LABELS[entity_type]} '
                f'{_entity_display_title(entity)} está pronto.'
            ),
            url=reverse(ENTITY_URL_TEMPLATES[entity_type], kwargs={'pk': entity.pk}),
        )
        return {
            'entity_type': entity_type,
            'entity_id': entity.pk,
            'usage_metadata': result.get('usage_metadata'),
        }
    except Exception as error:
        mark_summary_error(entity_type, entity_id, brokerage, error)
        raise
