"""Celery tasks for AI summaries."""

from celery import shared_task
from django.contrib.auth import get_user_model

from tenants.models import Brokerage

from .services import generate_summary, mark_summary_error


@shared_task(bind=True, max_retries=1, name='ai_agents.summarize')
def summarize(self, entity_type, entity_id, brokerage_id, user_id):
    brokerage = Brokerage.objects.get(pk=brokerage_id)
    user = get_user_model().objects.get(pk=user_id, brokerage=brokerage)
    try:
        return generate_summary(entity_type, entity_id, brokerage, user)
    except Exception as error:
        try:
            mark_summary_error(entity_type, entity_id, brokerage, error)
        except Exception:
            pass
        raise
