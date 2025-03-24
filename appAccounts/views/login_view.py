from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from appAccounts.forms import CustomUserCreationForm


def login(request):
    # If the user is already authenticated, redirect them accordingly
    if request.user.is_authenticated:
        if request.user.user_type.lower() == "admin":
            return redirect("appAdmin:dashboard")
        elif request.user.user_type.lower() == "secretariat":
            return redirect("appCmi:home")
        elif request.user.user_type.lower() == "cmi":
            return redirect("appCmi:home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)

            # Set a session variable for CMI users
            if user.user_type.lower() == "cmi":
                request.session["is_cmi_user"] = True
            else:
                request.session.pop("is_cmi_user", None)

            success_message = f"Welcome, {user.get_user_type_display()}!"
            messages.success(request, success_message)

            if user.user_type.lower() == "admin":
                return redirect("appAdmin:dashboard")
            elif user.user_type.lower() == "secretariat":
                return redirect("appCmi:home")
            elif user.user_type.lower() == "cmi":
                return redirect("appCmi:home")
        else:
            messages.error(
                request, "Sorry, wrong credentials or account is yet to be activated!"
            )
            return render(
                request,
                "login.html",
                {"error_message": "Invalid login credentials"},
            )

    return render(request, "login.html")
