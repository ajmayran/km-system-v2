from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from appAccounts.forms import CustomUserCreationForm
from appAccounts.models import CustomUser


# Create your views here.
def registration(request):
    # info = nav_info()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data["password"]
            user.set_password(
                password
            )  # Use set_password to hash the password with Argon2
            user.is_active = False  # Set user to inactive until email activation
            user.save()

            # Send activation email
            send_activation_code(request, user, user.email)

            message = "Please check your email to verify account."
            messages.success(request, message)
            return redirect("app_accounts:login")

        else:
            if form.errors:
                message = "Email already existed!"
                messages.error(request, message)
                return redirect("app_accounts:sign-up")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/registration.html", {"form": form})
