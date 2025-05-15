from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.html import strip_tags
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
import logging
from django.http import JsonResponse
import traceback

# Set up logger
logger = logging.getLogger(__name__)


@login_required
def send_reset_password_link(request):
    """
    View function to send a password reset link to the currently logged in user.
    Triggered from the user profile page.
    """
    if request.method != "POST":
        # If not POST, redirect to profile page
        return redirect("appCmi:cmi-profile")

    user = request.user
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    response_data = {"success": False, "message": "", "errors": {}}

    try:
        # Log attempt with user details for debugging
        logger.info(f"Password reset requested for user: {user.email} (ID: {user.pk})")

        if not user.is_active:
            error_msg = "Your account is not active. Please contact support."
            logger.warning(
                f"Reset password failed: Inactive account for user {user.email}"
            )
            messages.error(request, error_msg)
            response_data["message"] = error_msg

            if is_ajax:
                return JsonResponse(response_data)
            return redirect("appCmi:cmi-profile")

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

        # Log token creation details
        logger.info(
            f"Reset token created for user {user.email}: UID={uid}, token valid at {current_site.domain}"
        )

        # Send email with reset password link
        subject = "Password Reset Request"
        context = {
            "user": user,
            "reset_url": reset_url,
            "first_name": user.first_name,  # Add more user context fields as needed
            "request_ip": request.META.get("REMOTE_ADDR", "unknown"),
        }
        receiver_email = [user.email]
        template_name = "forgot-password/email-reset-pass.html"

        try:
            convert_to_html_content = render_to_string(template_name, context)
            plain_message = strip_tags(convert_to_html_content)
        except Exception as template_error:
            error_msg = f"Failed to render email template: {str(template_error)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            response_data["errors"]["template"] = error_msg
            response_data["message"] = "Email template error. Please contact support."

            if is_ajax:
                return JsonResponse(response_data)
            messages.error(request, response_data["message"])
            return redirect("appCmi:cmi-profile")

        # Send email and capture result
        try:
            yo_send_it = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=receiver_email,
                html_message=convert_to_html_content,
                fail_silently=False,  # Changed to False to catch email errors
            )

            # Log email sending details
            logger.info(
                f"Password reset email sent to {user.email}: {'Success' if yo_send_it else 'Failed'}"
            )

        except Exception as email_error:
            error_details = str(email_error)
            logger.error(
                f"Email sending error for {user.email}: {error_details}\n{traceback.format_exc()}"
            )
            response_data["errors"]["email"] = error_details
            response_data["message"] = "Failed to send email. Please try again later."

            if is_ajax:
                return JsonResponse(response_data)
            messages.error(request, response_data["message"])
            return redirect("appCmi:cmi-profile")

        if yo_send_it:
            success_msg = (
                "Password reset link sent to your email. Please check your inbox."
            )
            messages.success(request, success_msg)
            response_data["success"] = True
            response_data["message"] = success_msg
        else:
            error_msg = "Failed to send email. Please try again later."
            logger.warning(
                f"Email sending failed for user {user.email} - no exception but returned 0"
            )
            messages.error(request, error_msg)
            response_data["message"] = error_msg
            response_data["errors"]["email_send"] = "Email service returned 0"

    except Exception as e:
        # Catch any unexpected errors
        error_trace = traceback.format_exc()
        logger.critical(
            f"Unexpected error in password reset for {user.email}: {str(e)}\n{error_trace}"
        )
        response_data["message"] = (
            "An unexpected error occurred. Please try again later."
        )
        response_data["errors"]["unexpected"] = str(e)
        messages.error(request, response_data["message"])

    # Return JSON response if it's an AJAX request
    if is_ajax:
        return JsonResponse(response_data)

    return redirect("appCmi:cmi-profile")
