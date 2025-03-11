from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect


def update_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password == confirm_password:
            # Update the user's password and keep the user logged in
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated successfully.")
            return redirect(
                "app_general:general-settings"
            )  # Redirect to a success page or return JSON response
        else:
            messages.error(
                request, "New password and confirmation password do not match."
            )
    else:
        messages.error(
            request, "There was an error updating the password. Please check the form."
        )

    return render(request, "content/general/gen-account.html")
