from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings

def send_mail_with_html(subject, html_message, to_email, from_email = None):
    if isinstance(to_email, str):
        to = [to_email]
    else:
        to = to_email
    msg = EmailMultiAlternatives(
        subject=subject,
        from_email=from_email,
        to=to, 
        reply_to=[settings.SMTP_REPLY_TO]
    )
    msg.attach_alternative(html_message, 'text/html')
    msg.send()