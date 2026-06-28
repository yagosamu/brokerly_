from django import forms

from documents.models import Document


ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/csv',
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


class DocumentUploadForm(forms.ModelForm):
    content_type_id = forms.IntegerField(widget=forms.HiddenInput)
    object_id = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = Document
        fields = ('file', 'description')

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        if uploaded_file.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                f'Arquivo excede o limite de '
                f'{MAX_UPLOAD_SIZE // (1024 * 1024)} MB.'
            )
        mime_type = (
            getattr(uploaded_file, 'content_type', '')
            or 'application/octet-stream'
        )
        if mime_type not in ALLOWED_MIME_TYPES:
            raise forms.ValidationError(
                'Tipo de arquivo não permitido. Use PDF, imagem, Office ou texto.'
            )
        return uploaded_file
