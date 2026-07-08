from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User

from .services import ENTITY_MODELS, _get_entity, start_summary_processing
from .tasks import summarize


ALLOWED_SUMMARY_ROLES = (
    User.Role.OWNER,
    User.Role.MANAGER,
    User.Role.BROKER,
    User.Role.AGENT,
)


def _tenant_or_forbidden(request):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return None, JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
    return tenant, None


def _entity_or_response(entity_type, pk, tenant):
    if entity_type not in ENTITY_MODELS:
        return None, JsonResponse({'ok': False, 'error': 'Tipo de entidade inválido.'}, status=404)
    try:
        return _get_entity(entity_type, pk, tenant), None
    except Exception:
        return None, JsonResponse({'ok': False, 'error': 'Entidade não encontrada.'}, status=404)


@login_required
@require_POST
def trigger_summary(request, entity_type, pk):
    tenant, response = _tenant_or_forbidden(request)
    if response:
        return response
    if request.user.role not in ALLOWED_SUMMARY_ROLES:
        return JsonResponse({'ok': False, 'error': 'Acesso negado para o seu perfil.'}, status=403)
    entity, response = _entity_or_response(entity_type, pk, tenant)
    if response:
        return response
    if entity.ai_summary_status == 'processing':
        return JsonResponse(
            {'ok': False, 'status': 'processing', 'error': 'Resumo em processamento.'},
            status=409,
        )
    start_summary_processing(entity)
    summarize.delay(entity_type, entity.pk, tenant.pk, request.user.pk)
    return JsonResponse({'ok': True, 'status': 'processing'}, status=202)


@login_required
@require_GET
def summary_status(request, entity_type, pk):
    tenant, response = _tenant_or_forbidden(request)
    if response:
        return response
    entity, response = _entity_or_response(entity_type, pk, tenant)
    if response:
        return response
    updated_at = entity.ai_summary_updated_at.isoformat() if entity.ai_summary_updated_at else None
    return JsonResponse({
        'ok': True,
        'status': entity.ai_summary_status,
        'markdown': entity.ai_summary,
        'updated_at': updated_at,
    })
