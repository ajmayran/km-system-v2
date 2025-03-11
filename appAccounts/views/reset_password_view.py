# Description: This file contains the view for resetting the password of a user.
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.urls import reverse


def reset_password(request):
    if request.method == "POST":
        confirm_password = request.POST.get("password")
        email = request.POST.get("email")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            messages.error(request, "Email does not exist. Try registering an account!")
            return redirect("appAccounts:login")

        if not user.is_active:
            messages.error(
                request, "Your account is not active. Please contact support."
            )
            return redirect("appAccounts:login")

        # hash the password
        user.set_password(confirm_password)
        user.save()
        messages.success(request, "Password updated successfully.")
        return JsonResponse({"redirect_url": reverse("appAccounts:login")})
