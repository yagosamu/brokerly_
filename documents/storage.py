import os
import uuid


def document_upload_path(instance, filename):
    """Build a tenant-segregated path with an unguessable file name."""

    extension = os.path.splitext(filename)[1].lower()
    app_label = (
        instance.content_type.app_label
        if instance.content_type_id
        else 'misc'
    )
    return (
        f'brokerage_{instance.brokerage_id}/{app_label}/'
        f'{uuid.uuid4().hex}{extension}'
    )
