from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.html import strip_tags
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


def enter_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email does not exist. Try registering an account!")
            return redirect("appAccounts:login")

        if not user.is_active:
            messages.error(
                request, "Your account is not active. Please contact support."
            )
            return redirect("appAccounts:login")

        # Generate password reset token
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Build reset password URL
        current_site = get_current_site(request)
        protocol = "https" if request.is_secure() else "http"
        reset_url = reverse_lazy(
            "appAccounts:reset-pass-confirm", kwargs={"uidb64": uid, "token": token}
        )
        reset_url = f"{protocol}://{current_site.domain}{reset_url}"

        # Send email with reset password link
        subject = "Password Reset Request"
        context = {
            "user": user,
            "reset_url": reset_url,
        }
        receiver_email = [user.email]
        template_name = "forgot-password/email-reset-pass.html"
        convert_to_html_content = render_to_string(template_name, context)
        plain_message = strip_tags(convert_to_html_content)

        yo_send_it = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=receiver_email,
            html_message=convert_to_html_content,
            fail_silently=True,
        )

        if yo_send_it:
            messages.success(
                request, "Email sent successfully. Check your email for instructions."
            )
        else:
            messages.error(request, "No internet connection.")

        return redirect("appAccounts:login")

    return render(request, "forgot-password/enter-email.html")
