import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from accounts.models import User

from .agent import build_chat_agent
from .models import ChatMessage, ChatSession
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


def _sse_event(payload):
    return f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'


def _session_or_404(request, session_id):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        raise Http404
    try:
        return ChatSession.objects.get(
            pk=session_id,
            brokerage=tenant,
            user=request.user,
            is_archived=False,
        )
    except ChatSession.DoesNotExist:
        raise Http404


def _message_payload(message):
    return {
        'id': message.id,
        'role': message.role,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
    }


def _session_payload(session):
    return {
        'id': session.id,
        'title': session.title,
        'last_message_at': (
            session.last_message_at.isoformat() if session.last_message_at else None
        ),
        'created_at': session.created_at.isoformat(),
        'url': reverse('ai_agents:chat_stream', kwargs={'session_id': session.id}),
    }


def _history_messages(session):
    messages = list(session.messages.order_by('-created_at')[:20])
    messages.reverse()
    return [
        (message.role, message.content)
        for message in messages
        if message.role in (ChatMessage.Role.USER, ChatMessage.Role.ASSISTANT)
    ]


def _extract_token(event):
    if isinstance(event, tuple) and event:
        message = event[0]
    else:
        message = event
    content = getattr(message, 'content', '')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(
            item.get('text', '')
            for item in content
            if isinstance(item, dict)
        )
    return ''


def _extract_tool_calls(event):
    if isinstance(event, tuple) and event:
        message = event[0]
    else:
        message = event
    tool_calls = getattr(message, 'tool_calls', None)
    return tool_calls or None


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


class ChatPageView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_agents/chat.html'

    def get_template_names(self):
        try:
            get_template(self.template_name)
        except TemplateDoesNotExist:
            return ['home.html']
        return [self.template_name]


class ChatSessionListCreateView(LoginRequiredMixin, View):
    """GET lists active sessions, POST creates a new session."""

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
        sessions = ChatSession.objects.filter(
            brokerage=tenant,
            user=request.user,
            is_archived=False,
        )
        return JsonResponse({
            'ok': True,
            'sessions': [_session_payload(session) for session in sessions],
        })

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
        title = (request.POST.get('title') or 'Nova conversa').strip()
        session = ChatSession.objects.create(
            brokerage=tenant,
            user=request.user,
            title=title[:120] or 'Nova conversa',
            last_message_at=timezone.now(),
        )
        return JsonResponse({'ok': True, **_session_payload(session)}, status=201)


class ChatSessionRenameView(LoginRequiredMixin, View):
    """POST title to rename a session."""

    def post(self, request, session_id):
        session = _session_or_404(request, session_id)
        title = (request.POST.get('title') or '').strip()
        if not title:
            return JsonResponse({'ok': False, 'error': 'Informe um título.'}, status=400)
        session.title = title[:120]
        session.save(update_fields=['title', 'updated_at'])
        return JsonResponse({'ok': True, **_session_payload(session)})


class ChatSessionDeleteView(LoginRequiredMixin, View):
    """POST archives a session."""

    def post(self, request, session_id):
        session = _session_or_404(request, session_id)
        session.is_archived = True
        session.save(update_fields=['is_archived', 'updated_at'])
        return JsonResponse({'ok': True})


class ChatMessageStreamView(LoginRequiredMixin, View):
    """POST a message and stream the assistant response with SSE."""

    def post(self, request, session_id):
        session = _session_or_404(request, session_id)
        content = (request.POST.get('content') or '').strip()
        if not content:
            return JsonResponse({'ok': False, 'error': 'Informe uma mensagem.'}, status=400)

        user_message = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=content,
        )
        now = timezone.now()
        session.last_message_at = now
        session.save(update_fields=['last_message_at', 'updated_at'])
        history = _history_messages(session)

        def event_stream():
            if not settings.OPENAI_API_KEY:
                message = 'A chave da OpenAI não está configurada.'
                assistant_message = ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.ASSISTANT,
                    content=f'[Erro: {message}]',
                )
                yield _sse_event({'type': 'error', 'message': message})
                yield _sse_event({'type': 'done', 'message_id': assistant_message.id})
                return

            chunks = []
            tool_log = []
            try:
                agent = build_chat_agent(session.brokerage)
                for event in agent.stream(
                    {'messages': history},
                    stream_mode='messages',
                ):
                    token = _extract_token(event)
                    tool_calls = _extract_tool_calls(event)
                    if tool_calls:
                        tool_log.append(tool_calls)
                    if token:
                        chunks.append(token)
                        yield _sse_event({'type': 'token', 'content': token})
                full_response = ''.join(chunks).strip()
                assistant_message = ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.ASSISTANT,
                    content=full_response,
                    tool_calls=tool_log or None,
                )
                session.last_message_at = timezone.now()
                session.save(update_fields=['last_message_at', 'updated_at'])
                yield _sse_event({
                    'type': 'done',
                    'message_id': assistant_message.id,
                })
            except Exception as error:
                message = str(error)[:300] or 'Erro ao gerar resposta.'
                assistant_message = ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.ASSISTANT,
                    content=f'[Erro: {message}]',
                )
                session.last_message_at = timezone.now()
                session.save(update_fields=['last_message_at', 'updated_at'])
                yield _sse_event({'type': 'error', 'message': message})
                yield _sse_event({'type': 'done', 'message_id': assistant_message.id})

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
