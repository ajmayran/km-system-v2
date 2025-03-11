from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from appAccounts.forms import CustomUserCreationForm
from appAccounts.views import activation_code_view


# Create your views here.
def registration(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Add first_name and last_name from the form
            user.first_name = request.POST.get("first_name", "")
            user.last_name = request.POST.get("last_name", "")

            # Get password from the correct field name
            password = request.POST.get("password1")
            user.set_password(password)  # Use set_password to hash with Argon2

            user.is_active = False  # Set user to inactive until email activation
            user.save()

            # Send activation email
            activation_code_view.send_activation_code(request, user, user.email)

            message = "Please check your email to verify account."
            messages.success(request, message)
            return redirect("appAccounts:login")

        else:
            # Display specific form errors instead of a generic message
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field}: {error}")

            # Return the form with errors to display them in the template
            return render(request, "registration/registration.html", {"form": form})
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/registration.html", {"form": form})
