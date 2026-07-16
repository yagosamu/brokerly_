from importlib import import_module

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.views import View
from django.views.generic import TemplateView

from accounts.models import User
from reports.models import ReportJob
from reports.registry import REPORTS
from reports.tasks import generate_pdf_report


ALLOWED_REPORT_ROLES = (
    User.Role.OWNER,
    User.Role.MANAGER,
    User.Role.BROKER,
)

PRODUCTIVITY_ROLES = (
    User.Role.OWNER,
    User.Role.MANAGER,
)


def _tenant_or_forbidden(request):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return None, JsonResponse({'ok': False, 'error': 'Conta sem corretora.'}, status=403)
    return tenant, None


def _role_allowed(user, report_type=None):
    if report_type == 'produtividade':
        return user.role in PRODUCTIVITY_ROLES
    return user.role in ALLOWED_REPORT_ROLES


def _report_or_404(report_type):
    try:
        return REPORTS[report_type]
    except KeyError as error:
        raise Http404 from error


def _collect_params(request, report):
    return {
        key: request.GET.get(key) or request.POST.get(key)
        for key in report['filters']
        if request.GET.get(key) or request.POST.get(key)
    }


def _import_callable(path):
    module_path, function_name = path.rsplit('.', 1)
    return getattr(import_module(module_path), function_name)


class ReportPermissionMixin(LoginRequiredMixin):
    report_type = None

    def dispatch(self, request, *args, **kwargs):
        report_type = kwargs.get('report_type', self.report_type)
        if not _role_allowed(request.user, report_type):
            return JsonResponse({'ok': False, 'error': 'Acesso negado.'}, status=403)
        return super().dispatch(request, *args, **kwargs)


class ReportMenuView(ReportPermissionMixin, TemplateView):
    template_name = 'reports/menu.html'

    def get_template_names(self):
        try:
            get_template(self.template_name)
        except TemplateDoesNotExist:
            return ['home.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = REPORTS
        return context


class ReportDetailView(ReportPermissionMixin, TemplateView):
    template_name = 'reports/report.html'

    def get_template_names(self):
        try:
            get_template(self.template_name)
        except TemplateDoesNotExist:
            return ['home.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_type = self.kwargs['report_type']
        report = _report_or_404(report_type)
        context.update({
            'report_type': report_type,
            'report': report,
            'reports': REPORTS,
            'params': _collect_params(self.request, report),
        })
        return context


class ReportCsvView(ReportPermissionMixin, View):
    def get(self, request, report_type):
        tenant, response = _tenant_or_forbidden(request)
        if response:
            return response
        report = _report_or_404(report_type)
        params = _collect_params(request, report)
        generator = _import_callable(report['csv_generator'])
        filename, data = generator(tenant, params)
        response = HttpResponse(data, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ReportPdfRequestView(ReportPermissionMixin, View):
    def post(self, request, report_type):
        tenant, response = _tenant_or_forbidden(request)
        if response:
            return response
        report = _report_or_404(report_type)
        params = _collect_params(request, report)
        job = ReportJob.objects.create(
            brokerage=tenant,
            requested_by=request.user,
            report_type=report_type,
            params=params,
        )
        generate_pdf_report.delay(job.id)
        return JsonResponse({'ok': True, 'job_id': job.id}, status=202)


class ReportPdfStatusView(ReportPermissionMixin, View):
    def get(self, request, job_id):
        job = _job_or_404(request, job_id)
        return JsonResponse({
            'ok': True,
            'id': job.id,
            'status': job.status,
            'error_message': job.error_message,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'download_url': (
                f'/relatorios/pdf/download/{job.id}/'
                if job.status == ReportJob.Status.DONE else ''
            ),
        })


class ReportPdfDownloadView(ReportPermissionMixin, View):
    def get(self, request, job_id):
        job = _job_or_404(request, job_id)
        if job.status != ReportJob.Status.DONE or not job.file:
            raise Http404
        return FileResponse(
            job.file.open('rb'),
            as_attachment=True,
            filename=job.file.name.rsplit('/', 1)[-1],
            content_type='application/pdf',
        )


def _job_or_404(request, job_id):
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        raise Http404
    try:
        job = ReportJob.objects.get(
            pk=job_id,
            brokerage=tenant,
            requested_by=request.user,
        )
    except ReportJob.DoesNotExist as error:
        raise Http404 from error
    if not _role_allowed(request.user, job.report_type):
        raise Http404
    return job
