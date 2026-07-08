from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task(name='notifications.send_email')
def send_email(*, subject, body, from_email, to, html_body=None, headers=None):
    """Send a single email asynchronously."""
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to if isinstance(to, list) else [to],
        headers=headers or {},
    )
    if html_body:
        message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)
    return {'sent_to': message.to}


@shared_task(name='notifications.send_password_reset_email')
def send_password_reset_email(
    *,
    subject,
    body,
    from_email,
    to,
    html_body=None,
):
    return send_email(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        html_body=html_body,
    )
