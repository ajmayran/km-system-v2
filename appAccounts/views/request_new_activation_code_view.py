from django.shortcuts import render, redirect, get_object_or_404
from appAccounts.tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from .new_activation_code_view import send_new_activation_code


def request_new_activation_code(request):
    if request.method == "POST":
        email = request.POST.get(
            "email"
        )  # Assuming you have a form field with name 'email'

        CustomUser = get_user_model()

        try:
            user = CustomUser.objects.get(email=email)

            if user.is_active:
                messages.info(
                    request,
                    "Your account is already active. You can log in.",
                )
            else:
                # Send activation email again
                send_new_activation_code(user, request)
                messages.success(
                    request,
                    f"Activation code has been sent again to {email}. Please check your email.",
                )
        except CustomUser.DoesNotExist:
            messages.error(
                request,
                "Email does not exist! Please register to create an account.",
            )

        return redirect("appAccounts:login")  # Redirect to login page in all cases

    return render(request, "registration/request-new-code.html")
