import os

from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.pop('CELERY_RESULT_BACKEND', None)

app = Celery('brokerly')
app.config_from_object('django.conf:settings', namespace='CELERY')
configured_result_backend = settings.CELERY_RESULT_BACKEND
configured_result_extended = settings.CELERY_RESULT_EXTENDED
configured_cache_backend = settings.CELERY_CACHE_BACKEND
os.environ.pop('CELERY_RESULT_BACKEND', None)
app.conf.update(
    result_backend=configured_result_backend,
    result_extended=configured_result_extended,
    cache_backend=configured_cache_backend,
)
app.autodiscover_tasks()
