"""LangGraph agent runners for AI summaries and chat."""

from django.conf import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .prompts import CHAT_SYSTEM_PROMPT, PROMPTS
from .tools import build_tenant_tools


def _get_final_message(result):
    messages = result.get('messages', [])
    if not messages:
        return None
    return messages[-1]


def run_summary_agent(entity_type, entity_id, brokerage):
    model = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
        timeout=55,
    )
    tools = build_tenant_tools(brokerage, entity_type, entity_id)
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=PROMPTS[entity_type],
    )
    result = agent.invoke({
        'messages': [
            (
                'user',
                'Gere o resumo executivo desta entidade usando as ferramentas '
                'disponíveis. Retorne apenas Markdown pronto para exibição.',
            ),
        ],
    })
    final_message = _get_final_message(result)
    markdown = getattr(final_message, 'content', '') if final_message else ''
    usage_metadata = getattr(final_message, 'usage_metadata', None)
    return {
        'markdown': markdown.strip(),
        'usage_metadata': usage_metadata,
    }


def build_chat_agent(brokerage):
    model = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        streaming=True,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
        timeout=55,
        max_retries=0,
    )
    brokerage_name = getattr(brokerage, 'trade_name', '') or str(brokerage)
    return create_react_agent(
        model=model,
        tools=build_tenant_tools(brokerage),
        prompt=CHAT_SYSTEM_PROMPT.format(brokerage_name=brokerage_name),
    )
