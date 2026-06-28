from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    FileResponse,
    Http404,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, View
from django.views.generic.edit import FormView

from base.mixins import RoleRequiredMixin
from documents.forms import DocumentUploadForm
from documents.models import Document


def get_tenant_content_object(content_type, object_id, tenant):
    """Return the parent object only when it belongs to the request tenant."""

    model_class = content_type.model_class()
    if model_class is None:
        raise Http404
    try:
        content_object = model_class._default_manager.get(pk=object_id)
    except ObjectDoesNotExist as error:
        raise Http404 from error

    if content_object._meta.label_lower == 'tenants.brokerage':
        if content_object.pk != tenant.pk:
            raise Http404
    elif getattr(content_object, 'brokerage_id', None) != tenant.pk:
        raise Http404
    return content_object


class ProtectedDocumentDownloadView(LoginRequiredMixin, View):
    """Stream a document only when it and its parent belong to the tenant."""

    def get(self, request, pk):
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            raise Http404
        try:
            document = Document.objects.get(pk=pk, brokerage=tenant)
        except Document.DoesNotExist as error:
            raise Http404 from error

        get_tenant_content_object(
            document.content_type,
            document.object_id,
            tenant,
        )
        response = FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.original_name,
        )
        if document.mime_type:
            response['Content-Type'] = document.mime_type
        return response


class DocumentUploadView(RoleRequiredMixin, FormView):
    form_class = DocumentUploadForm
    allowed_roles = ('owner', 'manager', 'broker')

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        content_type_id = form.cleaned_data['content_type_id']
        object_id = form.cleaned_data['object_id']
        try:
            content_type = ContentType.objects.get_for_id(content_type_id)
        except ContentType.DoesNotExist:
            return HttpResponseBadRequest('Tipo de conteúdo inválido.')

        get_tenant_content_object(
            content_type,
            object_id,
            self.request.tenant,
        )
        uploaded_file = form.cleaned_data['file']
        document = Document.objects.create(
            brokerage=self.request.tenant,
            content_type=content_type,
            object_id=object_id,
            file=uploaded_file,
            original_name=uploaded_file.name,
            mime_type=getattr(uploaded_file, 'content_type', '') or '',
            size_bytes=uploaded_file.size,
            description=form.cleaned_data.get('description', ''),
            uploaded_by=self.request.user,
        )

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    'ok': True,
                    'id': document.id,
                    'original_name': document.original_name,
                    'size_kb': document.size_kb,
                    'download_url': f'/anexos/{document.id}/baixar/',
                }
            )
        next_url = self.request.POST.get('next') or '/'
        return redirect(next_url)


class DocumentDeleteView(RoleRequiredMixin, DeleteView):
    model = Document
    allowed_roles = ('owner', 'manager')
    success_url = reverse_lazy('home')

    def get_queryset(self):
        return Document.objects.filter(brokerage=self.request.tenant)

    def get_success_url(self):
        return self.request.POST.get('next') or super().get_success_url()
