from smtplib import SMTPException

from celery import shared_task
from django.core.mail import send_mail


@shared_task(
    autoretry_for=(OSError, SMTPException),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    ignore_result=True,
)
def send_post_share_email(subject, message, recipient):
    return send_mail(
        subject,
        message,
        from_email=None,
        recipient_list=[recipient],
        fail_silently=False,
    )
