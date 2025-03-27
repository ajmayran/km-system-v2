from utils.get_models import get_active_models
from django.shortcuts import render
from appCmi.forms import ForumForm
from django.shortcuts import redirect
import logging
from django.contrib import messages
from appAdmin.models import Commodity
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def cmi_forum(request):
    """Handles forum data aggregation and rendering for the forum page."""

    # Fetch active models
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    context = {
        "commodities": commodities,
        "useful_links": useful_links,
        "knowledge_resources": knowledge_resources,
    }

    return render(request, "pages/cmi-forum.html", context)


def forum_post_question(request):
    if request.method == "POST":
        form = ForumForm(request.POST)
        if form.is_valid():
            try:
                forum = form.save(commit=False)
                forum.author = request.user
                forum.save()

                # Get commodity_ids from either source
                commodity_ids = request.POST.get(
                    "commodity_ids", ""
                ) or request.POST.get("commodity_id", "")

                # Use the helper function to handle commodity associations
                _associate_commodities_with_forum(forum, commodity_ids)

                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True})

                messages.success(request, "Your question has been posted successfully.")
                return redirect("appCmi:cmi-forum")
            except Exception as e:
                logger.error(f"Error in forum post: {str(e)}")
        else:
            logger.error(f"Form invalid: {form.errors}")

    return render(request, "pages/cmi-forum.html", {"form": ForumForm()})


def _associate_commodities_with_forum(forum, commodity_ids_string):
    """
    Helper function to associate commodities with a forum post.

    Args:
        forum: The Forum model instance
        commodity_ids_string: Comma-separated string of commodity IDs
    """
    if not commodity_ids_string:
        return

    commodity_ids = commodity_ids_string.split(",")
    logger.debug(f"Processing commodity IDs: {commodity_ids}")

    # Bulk fetch commodities to minimize database queries
    if commodity_ids:
        selected_commodities = Commodity.objects.filter(commodity_id__in=commodity_ids)

        # Add all selected commodities to the forum in one operation
        forum.commodity_id.add(*selected_commodities)
