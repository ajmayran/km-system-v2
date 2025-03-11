from django.shortcuts import render, redirect, get_object_or_404
from appAccounts.tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages


def activate(request, uidb64, token):
    CustomUser = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None:
        if user.is_active:
            messages.info(request, "Your account is already active. You can log in.")
        elif account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request,
                "Thank you for your email confirmation. Now you can login to your account.",
            )
        else:
            messages.error(
                request,
                "Activation link is invalid or has expired! Please register again. Thank you!",
            )
    else:
        messages.error(
            request,
            "Activation link is invalid or has expired! Please register again. Thank you!",
        )

    return redirect("appAccounts:login")
