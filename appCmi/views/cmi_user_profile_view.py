from django.shortcuts import render
from utils.get_models import get_active_models
from appAccounts.models import Profile
from appAccounts.forms import ProfileForm, CustomUserUpdateForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from utils.user_control import user_access_required
from appAdmin.models import About

# Create your views here.
@user_access_required(["admin", "cmi"], error_type=404)
def display_cmi_profile(request):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    user = request.user
    about_list = About.objects.all() 
    # Try to get the profile, set to None if it doesn't exist
    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # Set default profile picture path if profile doesn't exist
        user_profile = None

    context = {
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "user": user,
        "user_profile": user_profile,
        "default_profile_image": "assets/images/default_profile.png",
        "about_list": about_list,
    }
    return render(request, "pages/cmi-user-profile.html", context)


@user_access_required(["admin", "cmi"], error_type=404)
def upload_profile_picture(request):
    """View function to handle profile picture uploads using ProfileForm."""
    if request.method == "POST":
        # Check if user already has a profile
        try:
            profile = Profile.objects.get(user=request.user)
            # If profile exists, use instance in the form
            form = ProfileForm(request.POST, request.FILES, instance=profile)
        except Profile.DoesNotExist:
            # Create a new form without instance
            form = ProfileForm(request.POST, request.FILES)

        if form.is_valid():
            if not hasattr(form, "instance") or not form.instance.pk:
                # This is a new profile
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
            else:
                # Just save the existing profile with new image
                profile = form.save()

            # Handle AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Profile picture updated successfully",
                        "image_url": profile.picture.url,
                    }
                )

            # Regular form submission
            messages.success(request, "Profile picture updated successfully")
            return redirect("profile")  # Redirect to profile page
        else:
            # Form validation failed
            error_message = "Invalid image file. Please try again."

            # Get the first error message if available
            if form.errors:
                error_message = next(iter(form.errors.values()))[0]

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_message})

            messages.error(request, error_message)
            return redirect("profile")

    # GET request or other methods not supported
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": False, "message": "Method not allowed"})

    return redirect("profile")


@user_access_required(["admin", "cmi"], error_type=404)
def update_user_info(request):
    """
    View function to handle user information updates.

    Primarily handles POST requests for AJAX form submissions.
    Validates all user input and provides JSON response for success/failure.
    """
    user = request.user
    if request.method == "POST":
        # Create a form instance with the POST data
        form = CustomUserUpdateForm(request.POST, instance=user)

        if form.is_valid():
            # Save the form data to update the user
            form.save()

            # Add success message
            messages.success(request, "Your profile has been updated successfully.")

            # For AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Profile updated successfully"}
                )

            # For regular form submissions - redirect to the profile page
            return redirect("profile")
        else:
            # Add error message
            messages.error(request, "Please correct the errors below.")

            # For AJAX requests with form errors
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Please correct the errors below",
                        "errors": form.errors,
                    }
                )

    # For non-AJAX GET requests or invalid POST submissions without AJAX
    form = CustomUserUpdateForm(instance=user)
    context = {"form": form, "user": user}
    return render(request, "pages/cmi-user-profile.html", context)
