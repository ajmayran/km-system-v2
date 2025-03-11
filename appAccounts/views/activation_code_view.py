from django.shortcuts import render, redirect, get_object_or_404
from appAccounts.tokens import account_activation_token
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import send_mail


def send_activation_code(request, user, to_email):
    subject = "Activate Your Account"
    context = {
        "first_name": user.first_name,
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": account_activation_token.make_token(user),
        "protocol": "https" if request.is_secure() else "http",
    }

    receiver_email = [to_email]
    template_name = "registration/activation-code.html"
    convert_to_html_content = render_to_string(
        template_name=template_name, context=context
    )
    plain_message = strip_tags(convert_to_html_content)

    yo_send_it = send_mail(
        subject="Activate Your Account",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=receiver_email,  # recipient_list is self explainatory
        html_message=convert_to_html_content,
        fail_silently=True,  # Optional
    )
