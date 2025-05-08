from django.shortcuts import render, redirect
from utils.get_models import get_active_models
from appCmi.forms import MessageToAdminForm
from appCmi.models import MessageToAdmin
from django.contrib import messages


# Create your views here.
def message(request):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    context = {
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-message.html", context)


def send_message(request):
    """
    View for sending messages to the admin and displaying message history.
    Requires user authentication.
    """
    # Handle form submission
    if request.method == "POST":
        form = MessageToAdminForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your message has been sent successfully! We'll get back to you soon.",
            )
            return redirect(
                "appCmi:send_message"
            )  # Redirect to the same page after submission
        else:
            messages.error(
                request,
                "There was an error sending your message. Please check the form and try again.",
            )
    else:
        # Display empty form for GET requests
        form = MessageToAdminForm()

    # Get user's message history
    user_messages = MessageToAdmin.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    # Prepare context for the template
    context = {
        "form": form,
        "user_messages": user_messages,
    }

    # Render the template with the context
    return render(request, "pages/cmi-message.html", context)
