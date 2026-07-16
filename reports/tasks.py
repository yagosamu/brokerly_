from importlib import import_module

from celery import shared_task
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from reports.models import ReportJob
from reports.registry import REPORTS


def _import_callable(path):
    module_path, function_name = path.rsplit('.', 1)
    return getattr(import_module(module_path), function_name)


@shared_task(bind=True, name='reports.generate_pdf_report')
def generate_pdf_report(self, job_id):
    job = ReportJob.objects.select_related('brokerage', 'requested_by').get(pk=job_id)
    job.status = ReportJob.Status.PROCESSING
    job.error_message = ''
    job.save(update_fields=['status', 'error_message', 'updated_at'])
    try:
        report = REPORTS[job.report_type]
        generator = _import_callable(report['pdf_generator'])
        filename, data = generator(
            job.brokerage,
            job.params,
            user=job.requested_by.email,
        )
        job.file.save(filename, ContentFile(data), save=False)
        job.status = ReportJob.Status.DONE
        job.completed_at = timezone.now()
        job.save(update_fields=[
            'file',
            'status',
            'completed_at',
            'updated_at',
        ])
        Notification.objects.create(
            brokerage=job.brokerage,
            user=job.requested_by,
            type=Notification.Type.REPORT_READY,
            title=f'Relatório "{report["name"]}" pronto',
            message=f'Gerado em {timezone.localtime(job.completed_at):%d/%m/%Y %H:%M}.',
            url=reverse('reports:pdf_download', kwargs={'job_id': job.id}),
        )
        return {'job_id': job.id, 'status': job.status}
    except Exception as error:
        job.status = ReportJob.Status.ERROR
        job.error_message = str(error)[:1000]
        job.completed_at = timezone.now()
        job.save(update_fields=[
            'status',
            'error_message',
            'completed_at',
            'updated_at',
        ])
        Notification.objects.create(
            brokerage=job.brokerage,
            user=job.requested_by,
            type=Notification.Type.REPORT_READY,
            title='Erro no relatório',
            message=job.error_message,
            url=reverse('reports:pdf_status', kwargs={'job_id': job.id}),
        )
        raise
